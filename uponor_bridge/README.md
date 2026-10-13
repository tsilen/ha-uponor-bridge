# Uponor Bridge

Home Assistant app that passively listens to the Uponor Smatrix Base (X-145) RS485 bus and publishes thermostat data to MQTT.

**Read-only:** the bridge never transmits on the bus.

## Install

1. **Settings → Apps → App store** → ⋮ → **Repositories**
2. Add `https://github.com/tsilen/ha-uponor-bridge`
3. Install **Uponor Bridge**, set `serial_port` if needed, enable **Start on boot** and **Watchdog**, then **Start**

See [DOCS.md](DOCS.md) for configuration, entities and behaviour.
