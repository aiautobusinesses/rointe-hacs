# Rointe Nexa – Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://hacs.xyz/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/youruser/rointe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) that connects to the **Rointe Nexa** cloud platform. It allows you to control your Rointe radiators and heaters directly from Home Assistant.

---

## ✨ Features

- Login using your Rointe Nexa app credentials  
- Automatic token refresh (no password stored)  
- Real-time device updates via Firebase WebSocket  
- Automatic discovery of all your installations, zones and devices  
- Control climate entities:
  - Turn on/off (comfort/eco/ice)  
  - Set target temperature  
  - View current temperature and mode in Home Assistant  

---

## 📦 Installation

1. Copy the `rointe` folder into:  
```

<config>/custom_components/rointe

```
where `<config>` is your Home Assistant config directory.

2. Restart Home Assistant.

3. In HA, go to:  
**Settings → Devices & Services → Add Integration → Search for “Rointe”**

4. Enter your **Rointe Nexa email + password**.  
- Home Assistant exchanges this for a `refreshToken`.  
- Only the refresh token is stored; your password is not kept.

5. Your Rointe devices will appear as **Climate entities**.

---

## 📂 Directory Layout

```

custom_components/rointe/
├── **init**.py
├── api.py
├── auth.py
├── climate.py
├── config_flow.py
├── const.py
├── manifest.json
├── strings.json
└── translations/
└── en.json

```

---

## ⚠️ Notes

- Requires a valid Rointe Nexa cloud account (same as the mobile app).  
- This integration is **not official** and not affiliated with Rointe.  
- The Firebase API key in use is public (from Rointe’s own app) and not tied to your account.  
- Tokens are managed securely by Home Assistant; your password is not stored.  

---

## 🛠️ Roadmap

- [x] Enhanced HVAC modes (AUTO, HEAT_COOL)  
- [x] Preset modes (Comfort, Eco)  
- [x] Comprehensive error handling  
- [x] Device information display  
- [x] Improved configuration flow  
- [ ] Add support for scheduling (edit/view Rointe weekly programs)  
- [ ] Add service calls for advanced features (eco, anti-frost, etc.)  
- [ ] Improve device model discovery (power, nominal wattage, etc.)  

---

## 🧪 For Developers

If you're developing or testing this integration:

1. **Clone the repository**
2. **Set up local testing environment:**
   - Use Docker: `docker run -d --name ha-test -p 8123:8123 -v /path/to/config:/config ghcr.io/home-assistant/home-assistant:stable`
   - Copy `custom_components/rointe` to your HA's `custom_components` directory
   - Restart Home Assistant and configure the integration

3. **Testing checklist:**
   - Configuration flow works with valid credentials
   - All HVAC modes function correctly
   - Temperature setting works within valid ranges
   - WebSocket updates work in real-time
   - Error handling works for network issues

---

## 🙏 Credits

- Reverse-engineering of Rointe Nexa web app & API by community members.  
- Built with ❤️ for Home Assistant users.  
```