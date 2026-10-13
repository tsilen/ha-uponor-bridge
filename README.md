# Uponor Bridge for Home Assistant

A Home Assistant app (add-on) repository containing **Uponor Bridge**: a read-only, passive listener for the Uponor Smatrix Base (X-145) thermostat RS485 bus. It decodes thermostat traffic received through a USB-RS485 adapter and publishes room temperatures, setpoints and status to MQTT using Home Assistant MQTT discovery.

The bridge **never transmits** on the bus. It only listens.

## Requirements

- Home Assistant OS / Supervised with the **Mosquitto broker** app installed and running, and the MQTT integration set up
- A USB-RS485 adapter connected to the Uponor bus A/B terminals

## Installation

1. In Home Assistant go to **Settings → Apps → App store**, open the ⋮ menu → **Repositories**.
2. Add `https://github.com/tsilen/ha-uponor-bridge`.
3. Install **Uponor Bridge**, select your serial port in the configuration and start it.

See [uponor_bridge/DOCS.md](uponor_bridge/DOCS.md) for details.

## Credits

Protocol understanding is based on the ESPHome [`uponor_smatrix`](https://esphome.io/components/uponor_smatrix/) component.

## License

MIT
