#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -e

if ! bashio::services.available "mqtt"; then
    bashio::exit.nok "No MQTT service found. Install and start the Mosquitto broker add-on."
fi

MQTT_HOST="$(bashio::services mqtt 'host')"
MQTT_PORT="$(bashio::services mqtt 'port')"
MQTT_USER="$(bashio::services mqtt 'username')"
MQTT_PASS="$(bashio::services mqtt 'password')"
UPONOR_PORT="$(bashio::config 'serial_port')"
export MQTT_HOST MQTT_PORT MQTT_USER MQTT_PASS UPONOR_PORT

bashio::log.info "Listening (read-only) on ${UPONOR_PORT}, MQTT ${MQTT_HOST}:${MQTT_PORT}"
exec python3 -u /app/uponor_bridge.py
