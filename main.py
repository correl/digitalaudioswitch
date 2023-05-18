from machine import Pin, SPI, SoftI2C
import framebuf
import json
import machine
import network
import ubinascii
import utime

from umqtt.simple import MQTTClient

import ssd1306
import mcp4

VOLUME_MAX = 128

MQTT_KEEPALIVE = 60
MQTT_UPDATE_INTERVAL = 60


state = {
    "volume": {
        "left": 0,
        "right": 0,
    }
}
last_update = 0

i2c = SoftI2C(sda=Pin(2), scl=Pin(16))
oled_width = 128
oled_height = 32
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
buf = bytearray((oled_height // 8) * oled_width)
fbuf = framebuf.FrameBuffer1(buf, oled_width, oled_height)

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
    print((topic, msg))
    try:
        msg = json.loads(msg)
    except:
        return
    if volume := msg.get("volume"):
        if isinstance(volume.get("left"), int):
            pot.write(0, volume["left"])
        if isinstance(volume.get("right"), int):
            pot.write(1, volume["right"])


def loop():
    global mqtt, state, last_update

    state_changed = False
    PW0 = pot.read(0)
    PW1 = pot.read(1)

    if PW0 != state["volume"]["left"]:
        state["volume"]["left"] = PW0
        state_changed = True
    if PW1 != state["volume"]["right"]:
        state["volume"]["right"] = PW1
        state_changed = True

    if not sta_if.active():
        sta_if.active(True)
        sta_if.connect(settings["wifi"]["ssid"], settings["wifi"]["password"])

    network_status = "OFF"
    if sta_if.active():
        network_status = "ACT"
    if sta_if.isconnected():
        network_status = "OK"
        if not mqtt:
            mqtt = MQTTClient(mqtt_client_id, mqtt_broker, keepalive=MQTT_KEEPALIVE)
            mqtt.set_callback(on_message)
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

        if state_changed or utime.time() - last_update >= MQTT_UPDATE_INTERVAL:
            mqtt.publish(f"{mqtt_prefix}/status".encode(), b"online", retain=True)
            mqtt.publish(
                f"{mqtt_prefix}/state".encode(), json.dumps(state).encode(), retain=True
            )

            last_update = utime.time()
        mqtt.check_msg()
    oled.fill(0)
    oled.text(f"PW0: {PW0}", 0, 0)
    oled.text(f"PW1: {PW1}", 0, 10)
    oled.text(f"NET: {network_status}", 65, 0)
    oled.show()


while True:
    loop()
    utime.sleep(1)