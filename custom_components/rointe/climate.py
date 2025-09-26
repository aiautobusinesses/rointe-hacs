import logging
from typing import Optional, Dict, Any
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
    PRESET_ECO,
    PRESET_COMFORT,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, DEVICE_MODELS
from .ws import SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)

# Rointe supports OFF and HEAT modes
HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT]

# Rointe preset modes
PRESET_MODES = [PRESET_ECO, PRESET_COMFORT]

# Temperature limits for Rointe devices
MIN_TEMP = 5.0
MAX_TEMP = 35.0

# Mode-specific temperature ranges
MODE_TEMPERATURES = {
    HVACMode.OFF: {"min": 5.0, "max": 7.0, "default": 7.0},
    HVACMode.HEAT: {"min": 15.0, "max": 35.0, "default": 21.0},
}


class RointeDeviceError(Exception):
    """Error communicating with Rointe device."""
    pass


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Rointe climate entities."""
    _LOGGER.error("🌡️ CLIMATE platform setup STARTING for entry: %s", entry.entry_id)
    try:
        data = hass.data[DOMAIN][entry.entry_id]
        ws = data["ws"]
        devices = data["devices"]

        if not devices:
            _LOGGER.warning("No devices found during setup")
            return

        entities = []
        for dev in devices:
            try:
                device_id = dev.get("id")
                device_name = dev.get("name", "Unknown Device")
                zone_name = dev.get("zone", "Unknown Zone")

                if not device_id:
                    _LOGGER.error("Device missing ID: %s", dev)
                    continue

                entity_name = f"{zone_name} - {device_name}"
                entity = RointeHeater(hass, ws, device_id, entity_name, dev)
                entities.append(entity)
                _LOGGER.debug("Created climate entity for device %s: %s", device_id, entity_name)

            except Exception as e:
                _LOGGER.error("Error creating entity for device %s: %s", dev, e)
                continue

        if entities:
            _LOGGER.error("🔥 About to add %d entities to HA", len(entities))
            async_add_entities(entities, update_before_add=False)
            _LOGGER.info("Successfully set up %d Rointe climate entities", len(entities))
        else:
            _LOGGER.error("No valid climate entities created")

    except Exception as e:
        _LOGGER.error("Error setting up Rointe climate entities: %s", e)
        raise


class RointeHeater(ClimateEntity):
    """Representation of a Rointe heater."""

    def __init__(self, hass, ws, device_id: str, name: str, device_info: Optional[Dict[str, Any]] = None):
        """Initialize the Rointe heater entity."""
        self.hass = hass
        self.ws = ws
        self.device_id = device_id
        self._device_info = device_info or {}

        # Core attributes
        self._attr_name = name
        self._attr_unique_id = f"rointe_{device_id}"
        self._attr_icon = "mdi:radiator"
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_available = True

        # Climate attributes
        self._attr_hvac_modes = HVAC_MODES
        self._attr_preset_modes = PRESET_MODES
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature_step = 0.5
        self._attr_min_temp = 7.0
        self._attr_max_temp = 30.0
        self._attr_precision = 0.5

        # Initial state
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = 20.0
        self._attr_target_temperature = 21.0
        self._attr_preset_mode = PRESET_ECO
        self._attr_hvac_action = HVACAction.OFF

        # Legacy/backing variables
        self._current_temp = 20.0
        self._target_temp = 21.0
        self._available = True
        self._last_update_time = None

        # Device info
        self._device_model = self._device_info.get("model")
        self._device_power = self._device_info.get("power")
        self._device_version = self._device_info.get("version")
        self._device_type = self._device_info.get("type")
        self._device_serial = self._device_info.get("serialNumber")
        self._device_mac = self._device_info.get("mac")
        self._zone_name = self._device_info.get("zone")

        # Category
        self._device_category = None
        if self._device_model:
            for model_key, category in DEVICE_MODELS.items():
                if model_key.lower() in self._device_model.lower():
                    self._device_category = category
                    break
        if not self._device_category:
            self._device_category = "radiator"

        # Status
        self._device_status = self._device_info.get("deviceStatus", {})
        self._online = self._device_info.get("online", True)
        self._last_seen = self._device_info.get("lastSeen")

        # Connect to updates
        async_dispatcher_connect(hass, f"{SIGNAL_UPDATE}_{self.device_id}", self._handle_update)

        _LOGGER.error("🔥 RointeHeater created: %s (ID: %s)", name, self.device_id)

    async def async_added_to_hass(self):
        """When entity is added."""
        _LOGGER.error("🔥 async_added_to_hass for entity: %s", self._attr_name)
        self.schedule_update_ha_state()

    async def async_update(self):
        """Update entity state."""
        _LOGGER.debug("async_update called for %s", self._attr_name)
        pass

    @property
    def unique_id(self) -> str:
        return f"rointe_{self.device_id}"

    @property
    def hvac_action(self) -> str:
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        return HVACAction.HEATING

    @property
    def device_info(self) -> Dict[str, Any]:
        info = {
            "identifiers": {("rointe", self.device_id)},
            "name": self._attr_name,
            "manufacturer": "Rointe",
            "model": self._device_model or "Rointe Heater",
        }
        if self._device_version:
            info["sw_version"] = self._device_version
        if self._device_serial:
            info["serial_number"] = self._device_serial
        if self._zone_name:
            info["suggested_area"] = self._zone_name
        return info

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs = {
            "device_id": self.device_id,
            "device_category": self._device_category,
            "online": self._online,
        }
        if self._device_power:
            attrs["power_watts"] = self._device_power
        if self._device_model:
            attrs["device_model"] = self._device_model
        if self._device_version:
            attrs["device_version"] = self._device_version
        if self._device_type:
            attrs["device_type"] = self._device_type
        if self._device_serial:
            attrs["serial_number"] = self._device_serial
        if self._device_mac:
            attrs["mac_address"] = self._device_mac
        if self._zone_name:
            attrs["zone"] = self._zone_name
        if self._last_seen:
            attrs["last_seen"] = self._last_seen
        if self._last_update_time:
            attrs["last_update"] = self._last_update_time.isoformat()
        if self._device_status:
            attrs["device_status"] = self._device_status
        return attrs

    def _handle_update(self, state: dict):
        try:
            _LOGGER.debug("Received update for %s: %s", self.device_id, state)

            self._device_status = state.get("deviceStatus", self._device_status)
            self._online = state.get("online", self._online)
            self._last_seen = state.get("lastSeen", self._last_seen)

            # Current temperature
            if "temp" in state and isinstance(state["temp"], (int, float)):
                temp = float(state["temp"])
                if MIN_TEMP <= temp <= MAX_TEMP:
                    self._current_temp = temp
                    self._attr_current_temperature = temp

            # Target temperature
            if "um_max_temp" in state and isinstance(state["um_max_temp"], (int, float)):
                temp = float(state["um_max_temp"])
                if MIN_TEMP <= temp <= MAX_TEMP:
                    self._target_temp = temp
                    self._attr_target_temperature = temp

            # HVAC mode
            if "status" in state and isinstance(state["status"], str):
                status = state["status"].lower()
                if status == "comfort":
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_preset_mode = PRESET_COMFORT
                    self._attr_hvac_action = HVACAction.HEATING
                elif status == "eco":
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_preset_mode = PRESET_ECO
                    self._attr_hvac_action = HVACAction.HEATING
                elif status == "ice":
                    self._attr_hvac_mode = HVACMode.OFF
                    self._attr_preset_mode = None
                    self._attr_hvac_action = HVACAction.OFF

            self._available = True
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self.device_id, e)

    async def async_set_hvac_mode(self, hvac_mode: str):
        if hvac_mode not in HVAC_MODES:
            _LOGGER.error("Invalid HVAC mode: %s", hvac_mode)
            return

        try:
            updates = {}
            if hvac_mode == HVACMode.HEAT:
                updates = {"status": "comfort", "power": 2}
            elif hvac_mode == HVACMode.OFF:
                updates = {"status": "eco", "power": 1}

            _LOGGER.info("🔥 Setting hvac_mode=%s for %s: %s", hvac_mode, self.device_id, updates)
            await self.ws.send(self.device_id, updates)

            self._attr_hvac_mode = hvac_mode
            if hvac_mode == HVACMode.HEAT:
                self._attr_preset_mode = PRESET_COMFORT
                self._attr_hvac_action = HVACAction.HEATING
            else:
                self._attr_preset_mode = None
                self._attr_hvac_action = HVACAction.OFF

            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error setting HVAC mode %s for %s: %s", hvac_mode, self.device_id, e)
            self._available = False
            self.async_write_ha_state()
            raise RointeDeviceError(f"Failed to set HVAC mode: {e}")

    async def async_turn_on(self):
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self):
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str):
        try:
            updates = {}
            if preset_mode == PRESET_COMFORT:
                updates = {"status": "comfort", "power": 2}
            elif preset_mode == PRESET_ECO:
                updates = {"status": "eco", "power": 1}

            _LOGGER.info("🔥 Setting preset=%s for %s", preset_mode, self.device_id)
            await self.ws.send(self.device_id, updates)

            self._attr_preset_mode = preset_mode
            if preset_mode in [PRESET_COMFORT, PRESET_ECO]:
                self._attr_hvac_mode = HVACMode.HEAT
                self._attr_hvac_action = HVACAction.HEATING
            else:
                self._attr_hvac_mode = HVACMode.OFF
                self._attr_hvac_action = HVACAction.OFF

            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("❌ Error setting preset %s for %s: %s", preset_mode, self.device_id, e)
            raise RointeDeviceError(f"Failed to set preset: {e}")

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if not (self.min_temp <= temperature <= self.max_temp):
            _LOGGER.warning("Temperature %s outside valid range for %s", temperature, self.device_id)
            return

        self._target_temp = temperature
        self._attr_target_temperature = temperature

        updates = {"um_max_temp": temperature}
        await self.ws.send(self.device_id, updates)

        _LOGGER.info("🔥 Temperature set to %s for %s", temperature, self.device_id)
        self.schedule_update_ha_state()