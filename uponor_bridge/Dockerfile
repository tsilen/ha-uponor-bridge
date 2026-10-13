# Multi-arch base (aarch64 + amd64), Alpine 3.22, pinned release tag.
# Since Supervisor 2026.04 BUILD_FROM/build.yaml are no longer used: FROM must be explicit.
FROM ghcr.io/home-assistant/base:3.22-2026.10.0

# python3 3.12.x, py3-pyserial 3.5-r7 in Alpine 3.22 at time of writing.
# "~" pins the upstream version but accepts Alpine -rN rebuilds so builds don't break.
RUN apk add --no-cache "python3~3.12" "py3-pyserial~3.5"

COPY uponor_bridge.py /app/uponor_bridge.py
COPY run.sh /run.sh
RUN chmod a+x /run.sh

LABEL \
  io.hass.version="1.0.0" \
  io.hass.type="app" \
  io.hass.arch="aarch64|amd64"

CMD [ "/run.sh" ]
