from machine import Pin, SPI, SoftI2C
import framebuf
import json
import machine
import network
import ubinascii
import uasyncio
import utime

from umqtt.simple import MQTTClient

import cd4052
import ssd1306
import mcp4
from button import Button
from rotary_irq_esp import RotaryIRQ
from statetree import StateTree

VOLUME_MAX = const(128)

MQTT_KEEPALIVE = const(60)
MQTT_UPDATE_INTERVAL = const(60)

channels = ["LINE 1", "LINE 2", "LINE 3", "PHONO"]
state = StateTree(
    {
        "network": "OFF",
        "volume": {
            "left": 0,
            "right": 0,
            "muted": "OFF",
        },
        "channel": channels[0],
    }
)
last_update = 0

rotary = RotaryIRQ(
    33,
    32,
    0,
    max_val=128,
    range_mode=RotaryIRQ.RANGE_BOUNDED,
    pull_up=True,
    incr=4,
)
rotary_value = rotary.value()
rotary_button = Button(Pin(36, Pin.IN))

try:
    i2c = SoftI2C(sda=Pin(21), scl=Pin(22))
    oled_width = const(128)
    oled_height = const(32)
    oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
except Exception as e:
    print("WARNING: OLED unavailable:", e)
    oled = None

switch = cd4052.CD4052(18, 19, 23)
switch.select(0)

sta_if = network.WLAN(network.STA_IF)

spi = SPI(1)
cs = Pin(15, mode=Pin.OUT, value=1)
pot = mcp4.MCP4(spi, cs)

with open("settings.json", "r") as f:
    settings = json.load(f)

mqtt = None
mqtt_client_id = ubinascii.hexlify(machine.unique_id())
mqtt_broker = settings["mqtt"]["broker"]
mqtt_prefix = settings["mqtt"]["prefix"]


def on_message(topic, msg):
    print(f"MQTT <- [{topic}] {msg}")
    try:
        msg = json.loads(msg)
    except:
        return
    if volume := msg.get("volume"):
        if isinstance(volume.get("left"), int):
            pot.write(0, volume["left"])
        if isinstance(volume.get("right"), int):
            pot.write(1, volume["right"])
        if isinstance(volume.get("muted"), str):
            switch.mute(volume["muted"] == "ON")
    if isinstance(msg.get("channel"), str):
        try:
            switch.select(channels.index(msg["channel"]))
        except ValueError:
            print("WARNING: Attempted to select invalid channel", msg["channel"])


def loop():
    global mqtt, state, last_update, rotary, rotary_button, rotary_value

    rotary_button.update()
    if rotary_button.was_clicked():
        switch.toggle_mute()
    if rotary_button.was_double_clicked():
        if switch.channel() >= 3:
            switch.select(0)
        else:
            switch.select(switch.channel() + 1)

    state["volume"]["left"] = pot.read(0)
    state["volume"]["right"] = pot.read(1)
    state["volume"]["muted"] = "ON" if switch.muted() else "OFF"
    state["channel"] = channels[switch.channel()]

    if state.changed:
        # Volume changed externally
        rotary.set(value=max(state["volume"]["left"], state["volume"]["right"]))
        rotary_value = rotary.value()

    new_value = rotary.value()
    if rotary_value != new_value:
        print("Rotary:", new_value)
        state["volume"]["left"] = new_value
        state["volume"]["right"] = new_value
        pot.write(0, new_value)
        pot.write(1, new_value)
        rotary_value = new_value

    if not sta_if.active():
        print("Connecting to WiFi")
        sta_if.active(True)
        sta_if.connect(settings["wifi"]["ssid"], settings["wifi"]["password"])

    if sta_if.active() and not sta_if.isconnected():
        state["network"] = "ACT"
    if sta_if.isconnected():
        if state["network"] != "OK":
            ip, _, _, _ = sta_if.ifconfig()
            print(f"WIFI Connected to {sta_if.config('ssid')}")
            print(f"IP Address: {ip}")
            state["network"] = "OK"
        if not mqtt:
            print("Starting MQTT client")
            mqtt = MQTTClient(mqtt_client_id, mqtt_broker, keepalive=MQTT_KEEPALIVE)
            mqtt.set_callback(on_message)
            mqtt.set_last_will(f"{mqtt_prefix}/status", b"offline", retain=True)
            mqtt.connect()
            mqtt.subscribe(f"{mqtt_prefix}/set")
            mqtt_device = {
                "identifiers": mqtt_client_id,
                "manufacturer": "correl",
                "model": "digital-audio-switch",
                "name": "Digital Audio Switch",
            }

            mqtt.publish(
                f"homeassistant/number/digital-audio-switch/volume-left/config".encode(),
                json.dumps(
                    {
                        "name": "Digital Audio Switch Volume (Left)",
                        "command_topic": f"{mqtt_prefix}/set",
                        "command_template": '{"volume": {"left": {{value}}}}',
                        "state_topic": f"{mqtt_prefix}/state",
                        "value_template": "{{ value_json.volume.left }}",
                        "availability_topic": f"{mqtt_prefix}/status",
                        "min": 0,
                        "max": VOLUME_MAX,
                        "mode": "slider",
                        "step": 1,
                        "unique_id": "digital-audio-switch-volume-left",
                        "device": mqtt_device,
                    }
                ).encode(),
                retain=True,
            )
            mqtt.publish(
                f"homeassistant/number/digital-audio-switch/volume-right/config".encode(),
                json.dumps(
                    {
                        "name": "Digital Audio Switch Volume (Right)",
                        "command_topic": f"{mqtt_prefix}/set",
                        "command_template": '{"volume": {"right": {{value}}}}',
                        "state_topic": f"{mqtt_prefix}/state",
                        "value_template": "{{ value_json.volume.right }}",
                        "availability_topic": f"{mqtt_prefix}/status",
                        "min": 0,
                        "max": VOLUME_MAX,
                        "mode": "slider",
                        "step": 1,
                        "unique_id": "digital-audio-switch-volume-right",
                        "device": mqtt_device,
                    }
                ).encode(),
                retain=True,
            )
            mqtt.publish(
                f"homeassistant/number/digital-audio-switch/volume-master/config".encode(),
                json.dumps(
                    {
                        "name": "Digital Audio Switch Volume (Master)",
                        "command_topic": f"{mqtt_prefix}/set",
                        "command_template": '{"volume": {"right": {{value}}, "left": {{value}}}}',
                        "state_topic": f"{mqtt_prefix}/state",
                        "value_template": """
                            {%set values = value_json.volume.left,
                                           value_json.volume.right %}
                            {{ values|max }}
                        """,
                        "availability_topic": f"{mqtt_prefix}/status",
                        "min": 0,
                        "max": VOLUME_MAX,
                        "mode": "slider",
                        "step": 1,
                        "unique_id": "digital-audio-switch-volume-master",
                        "device": mqtt_device,
                    }
                ).encode(),
                retain=True,
            )
            mqtt.publish(
                f"homeassistant/switch/digital-audio-switch/mute/config".encode(),
                json.dumps(
                    {
                        "name": "Digital Audio Switch Mute",
                        "command_topic": f"{mqtt_prefix}/set",
                        "payload_on": '{"volume": {"muted": "ON"}}',
                        "payload_off": '{"volume": {"muted": "OFF"}}',
                        "state_on": "ON",
                        "state_off": "OFF",
                        "state_topic": f"{mqtt_prefix}/state",
                        "value_template": "{{ value_json.volume.muted }}",
                        "availability_topic": f"{mqtt_prefix}/status",
                        "unique_id": "digital-audio-switch-volume-mute",
                        "device": mqtt_device,
                    }
                ).encode(),
                retain=True,
            )
            mqtt.publish(
                f"homeassistant/select/digital-audio-switch/channel/config".encode(),
                json.dumps(
                    {
                        "name": "Digital Audio Switch Channel",
                        "command_topic": f"{mqtt_prefix}/set",
                        "command_template": '{"channel": "{{value}}"}',
                        "state_topic": f"{mqtt_prefix}/state",
                        "value_template": "{{ value_json.channel }}",
                        "availability_topic": f"{mqtt_prefix}/status",
                        "options": channels,
                        "unique_id": "digital-audio-switch-channel",
                        "device": mqtt_device,
                    }
                ).encode(),
                retain=True,
            )

        if state.changed or utime.time() - last_update >= MQTT_UPDATE_INTERVAL:
            topic = f"{mqtt_prefix}/state".encode()
            payload = json.dumps(state.dictionary).encode()
            print(f"MQTT -> [{topic}] {payload}")
            mqtt.publish(f"{mqtt_prefix}/status", b"online", retain=True)
            mqtt.publish(topic, payload, retain=True)
            last_update = utime.time()
        mqtt.check_msg()
    if oled and state.changed:
        oled.fill(0)
        oled.framebuf.rect(10, 0, 92, 8, 1)
        oled.framebuf.rect(
            12, 2, round(state["volume"]["left"] / VOLUME_MAX * 88), 4, 1, True
        )
        oled.framebuf.rect(10, 10, 92, 8, 1)
        oled.framebuf.rect(
            12, 12, round(state["volume"]["right"] / VOLUME_MAX * 88), 4, 1, True
        )
        oled.text("L", 0, 0)
        oled.text("R", 0, 10)
        oled.text(f"{state['volume']['left']:3d}", 104, 0)
        oled.text(f"{state['volume']['right']:3d}", 104, 10)
        if state["volume"]["muted"] == "ON":
            oled.framebuf.rect(40, 4, 4 * 8 + 2, 10, 0, True)
            oled.framebuf.rect(39, 3, 4 * 8 + 4, 12, 1)
            oled.framebuf.rect(38, 2, 4 * 8 + 6, 14, 0)
            oled.text("MUTE", 41, 5)
        oled.text(f"WiFi: {state['network']}", 0, 20)
        oled.text(f'{state["channel"]:>6}', 80, 20)
        oled.show()
    state.clean()


while True:
    loop()
    utime.sleep_ms(10)
