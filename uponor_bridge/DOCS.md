# Uponor Bridge

Listens **read-only** to the Uponor Smatrix Base X-145 RS485 bus (19200 8N1) through a USB
RS485 dongle and publishes each thermostat's room temperature, set point (dial), limits,
ECO and heating-demand state to Home Assistant via MQTT discovery. It never writes to the
bus: the serial port's `write` method is replaced with `None` at startup.

MQTT credentials are taken automatically from the Mosquitto broker add-on (`services: mqtt:need`).

## Options
- `serial_port`: the RS485 dongle. Default
  `/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG03WKE3-if00-port0`.

## Behaviour
- Serial error (dongle unplugged / not found): the process exits non-zero; with the
  watchdog enabled in the add-on UI the Supervisor restarts it.
- MQTT disconnect: reconnects internally every 10 s and re-sends discovery.
