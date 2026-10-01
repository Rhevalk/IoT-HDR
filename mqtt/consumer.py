import json
import asyncio
from fastapi_mqtt import FastMQTT, MQTTConfig
from mqtt.handler import handle_sensor_data

lock = asyncio.Lock()

mqtt_config = MQTTConfig(host="localhost", port=1883, keepalive=60)
fast_mqtt = FastMQTT(config=mqtt_config)


@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    fast_mqtt.client.subscribe("cinfarm/device/+/data")

@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    try:
        parts = topic.split("/")
        device_id = parts[2]
        data = json.loads(payload.decode())

        async with lock:
            handle_sensor_data(device_id, data)

    except Exception as e:
        print("Error parsing MQTT:", e)
