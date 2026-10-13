#!/usr/bin/env python3
"""Read-only Uponor Smatrix (X-145) RS485 -> Home Assistant MQTT bridge.
NEVER writes to the serial port. Stdlib + pyserial only (tiny built-in MQTT 3.1.1 publisher).
Protocol per ESPHome components/uponor_smatrix: [addr:4][id:1 val:2 BE]*n[crc16 modbus, LE]."""
import os, sys, json, time, socket, struct, argparse

ROOM, TARGET, TMIN, TMAX, ECO, DEMAND, MODE1, MODE2, EXT, HUM, OUTDOOR, REQ = \
    0x40, 0x3B, 0x37, 0x38, 0x3C, 0x3D, 0x3E, 0x3F, 0x41, 0x42, 0x2D, 0xFF
INVALID = 0x7FFF
MAXLEN = 64

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def f10_to_c(raw):
    return round((raw / 10.0 - 32) / 1.8, 1)

class Reassembler:
    """Finds frames by CRC, independent of inter-byte gaps."""
    def __init__(self): self.buf = bytearray()
    def feed(self, data):
        self.buf += data
        out = []
        while len(self.buf) >= 7:
            found = 0
            for n in range(7, min(len(self.buf), MAXLEN) + 1):
                if (n - 6) % 3 not in (0, 1):  # data = triples, or single 0xff request
                    continue
                f = self.buf[:n]
                if (f[-1] << 8 | f[-2]) == crc16(f[:-2]):
                    found = n; break
            if found:
                out.append(bytes(self.buf[:found])); del self.buf[:found]
            elif len(self.buf) >= MAXLEN:
                del self.buf[0]
            else:
                break
        return out

def parse(frame):
    addr = frame[:4].hex()
    body = frame[4:-2]
    if body[:1] == b"\xff":
        return addr, "request", {}
    fields = {body[i]: (body[i+1] << 8) | body[i+2] for i in range(0, len(body) - 2, 3)}
    kind = "thermostat" if ROOM in fields else "controller"
    return addr, kind, fields

def decode(fields):
    """Map raw fields -> HA states (entity keys only)."""
    s = {}
    def t(k, fid):
        v = fields.get(fid)
        if v is not None and v != INVALID: s[k] = f10_to_c(v)
    t("room_temperature", ROOM); t("target_temperature", TARGET)
    t("target_temperature_min", TMIN); t("target_temperature_max", TMAX)
    t("external_temperature", EXT)
    if ECO in fields and fields[ECO] != INVALID: s["eco_setback"] = round(fields[ECO] / 18.0, 1)  # F*10 delta -> C
    if HUM in fields:
        h = fields[HUM] & 0xFF
        if 0 < h <= 100: s["humidity"] = h
    if DEMAND in fields:
        d = fields[DEMAND]
        s["cooling_mode"] = "ON" if d & 0x1000 else "OFF"
        s["demand"] = "ON" if d & 0x0040 else "OFF"
    if MODE1 in fields: s["eco"] = "ON" if fields[MODE1] & 0x0008 else "OFF"
    return s

ENTITIES = {  # key: (component, device_class, unit, state_class)
    "room_temperature": ("sensor", "temperature", "°C", "measurement"),
    "target_temperature": ("sensor", "temperature", "°C", "measurement"),
    "target_temperature_min": ("sensor", "temperature", "°C", None),
    "target_temperature_max": ("sensor", "temperature", "°C", None),
    "external_temperature": ("sensor", "temperature", "°C", "measurement"),
    "eco_setback": ("sensor", "temperature", "°C", None),
    "humidity": ("sensor", "humidity", "%", "measurement"),
    "demand": ("binary_sensor", "heat", None, None),
    "cooling_mode": ("binary_sensor", None, None, None),
    "eco": ("binary_sensor", None, None, None),
}

class MQTT:
    """Minimal MQTT 3.1.1 QoS0 publisher (no external deps)."""
    def __init__(self, host, port, user, pw, cid="uponor_bridge"):
        self.a = (host, port, user, pw, cid); self.s = None; self.last = 0
    def _str(self, x): x = x.encode(); return struct.pack("!H", len(x)) + x
    def _len(self, n):
        o = b""
        while True:
            b = n % 128; n //= 128
            o += bytes([b | (0x80 if n else 0)])
            if not n: return o
    def connect(self):
        host, port, user, pw, cid = self.a
        self.s = socket.create_connection((host, port), timeout=10)
        flags = 0x02 | (0x80 if user else 0) | (0x40 if pw else 0) | 0x04 | 0x20  # clean, will retained
        p = self._str("MQTT") + bytes([4, flags]) + struct.pack("!H", 60) + self._str(cid)
        p += self._str("uponor_bridge/status") + self._str("offline")
        if user: p += self._str(user)
        if pw: p += self._str(pw)
        self.s.sendall(b"\x10" + self._len(len(p)) + p)
        ack = self.s.recv(4)
        if len(ack) < 4 or ack[3] != 0: raise ConnectionError("MQTT CONNACK %r" % ack)
        self.last = time.time()
        self.pub("uponor_bridge/status", "online", True)
    def pub(self, topic, payload, retain=False):
        if isinstance(payload, (dict, list)): payload = json.dumps(payload)
        p = self._str(topic) + str(payload).encode()
        self.s.sendall(bytes([0x30 | (1 if retain else 0)]) + self._len(len(p)) + p); self.last = time.time()
    def ping(self):
        if time.time() - self.last > 30:
            self.s.sendall(b"\xc0\x00"); self.last = time.time()
            self.s.setblocking(False)
            try: self.s.recv(64)
            except BlockingIOError: pass
            finally: self.s.settimeout(10)

class Bridge:
    def __init__(self, mqtt, prefix):
        self.m, self.prefix, self.announced, self.cache = mqtt, prefix, set(), {}
    def publish(self, addr, states):
        for k, v in states.items():
            if (addr, k) not in self.announced: self.discover(addr, k)
            if self.cache.get((addr, k)) != v:
                self.m.pub(f"uponor_bridge/{addr}/{k}", v, True); self.cache[(addr, k)] = v
    def discover(self, addr, key):
        comp, dc, unit, sc = ENTITIES[key]
        cfg = {"unique_id": f"uponor_{addr}_{key}", "object_id": f"uponor_{addr}_{key}",
               "translation_key": key, "has_entity_name": True, "name": key.replace("_", " ").capitalize(),
               "state_topic": f"uponor_bridge/{addr}/{key}", "availability_topic": "uponor_bridge/status",
               "device": {"identifiers": [f"uponor_{addr}"], "name": f"Uponor {addr}",
                          "manufacturer": "Uponor", "model": "Smatrix Base thermostat"}}
        if dc: cfg["device_class"] = dc
        if unit: cfg["unit_of_measurement"] = unit
        if sc: cfg["state_class"] = sc
        self.m.pub(f"{self.prefix}/{comp}/uponor_{addr}/{key}/config", cfg, True)
        self.announced.add((addr, key))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=os.environ.get("UPONOR_PORT",
        "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG03WKE3-if00-port0"))
    ap.add_argument("--baud", type=int, default=int(os.environ.get("UPONOR_BAUD", 19200)))
    ap.add_argument("--mqtt-host", default=os.environ.get("MQTT_HOST", "core-mosquitto"))
    ap.add_argument("--mqtt-port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    ap.add_argument("--mqtt-user", default=os.environ.get("MQTT_USER", ""))
    ap.add_argument("--mqtt-pass", default=os.environ.get("MQTT_PASS", ""))
    ap.add_argument("--prefix", default="homeassistant")
    ap.add_argument("--dry-run", action="store_true", help="print decoded values, no MQTT")
    a = ap.parse_args()
    import serial
    try:
        ser = serial.Serial(a.port, a.baud, bytesize=8, parity="N", stopbits=1, timeout=0.2)
    except serial.SerialException as e:
        print("cannot open serial port", a.port, ":", e, flush=True); sys.exit(2)
    ser.write = None  # hard guard: any write attempt raises TypeError
    rs = Reassembler()
    mq = br = None
    while True:
        try:
            if not a.dry_run and mq is None:
                mq = MQTT(a.mqtt_host, a.mqtt_port, a.mqtt_user, a.mqtt_pass); mq.connect()
                br = Bridge(mq, a.prefix); print("mqtt connected", flush=True)
            try:
                data = ser.read(256)
            except serial.SerialException as e:  # dongle unplugged etc.: exit so supervisor restarts us
                print("serial error:", e, "- exiting", flush=True); sys.exit(2)
            for fr in rs.feed(data):
                addr, kind, fields = parse(fr)
                if kind != "thermostat" and kind != "controller": continue
                st = decode(fields)
                if a.dry_run: print(time.strftime("%H:%M:%S"), addr, kind, st, flush=True)
                elif st: br.publish(addr, st)
            if mq: mq.ping()
        except (OSError, ConnectionError) as e:
            print("mqtt error:", e, "- retrying in 10s", flush=True)
            try: mq and mq.s.close()
            except Exception: pass
            mq = None; time.sleep(10)  # MQTT reconnects internally (Bridge re-sends discovery)

if __name__ == "__main__":
    main()
