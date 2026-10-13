# Uponor Bridge

Listens **read-only** to the Uponor Smatrix Base X-145 RS485 bus (19200 8N1) through a USB-RS485 adapter and publishes each thermostat's room temperature, set point (dial), limits, ECO and heating-demand state to Home Assistant via MQTT discovery.

The bridge **never writes** to the bus: the serial port's `write` method is replaced with `None` at startup.

## Requirements

- Home Assistant OS or Supervised
- **Mosquitto broker** app installed and running, with the MQTT integration set up
- A USB-RS485 adapter connected to the Uponor bus A/B terminals (common ground optional but recommended)

MQTT credentials are taken automatically from the Mosquitto broker app (`services: mqtt:need`).

## Installation

1. **Settings → Apps → App store** → ⋮ → **Repositories**
2. Add `https://github.com/tsilen/ha-uponor-bridge`
3. Install **Uponor Bridge**
4. On the Configuration tab, set `serial_port` to your adapter's path if it differs from the default
5. Enable **Start on boot** and **Watchdog**, then **Start**
6. Check the Log tab for `mqtt connected`

## Configuration

| Option | Description |
| --- | --- |
| `serial_port` | Path to the USB-RS485 adapter. Prefer a stable `/dev/serial/by-id/...` path so the port does not change across reboots. |

## Entities

Each thermostat on the bus appears as its own MQTT device. For every thermostat the app creates:

| Entity | Type | Description |
| --- | --- | --- |
| Room temperature | Sensor (°C) | Current room temperature |
| Target temperature | Sensor (°C) | Dial set point |
| Target temperature min | Sensor (°C) | Lower limit of the set-point range |
| Target temperature max | Sensor (°C) | Upper limit of the set-point range |
| ECO setback | Sensor (°C) | ECO mode temperature offset |
| Cooling mode | Binary sensor | On when the system is in cooling mode |
| Demand | Binary sensor | On when the thermostat requests heating (or cooling) |
| ECO | Binary sensor | On when ECO mode is active |

Values are published only when they change. Temperatures are reported in °C.

Devices are named by their bus address (for example `Uponor 10058c78`). Rename them and assign them to areas in Home Assistant as you like.

## Behaviour

- **Serial error** (adapter unplugged / not found): the process exits non-zero; with Watchdog enabled the Supervisor restarts it.
- **MQTT disconnect**: reconnects every 10 s and re-sends discovery.

## Credits

Protocol understanding is based on the ESPHome [`uponor_smatrix`](https://esphome.io/components/uponor_smatrix/) component.

## License

MIT
