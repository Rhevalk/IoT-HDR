from db.database import insert_sensor_data

def handle_sensor_data(device_id, data):

    print(f"[REALTIME] {device_id} -> {data}")

    insert_sensor_data(device_id, data)

    print(f"[DB SAVE] {device_id} -> {data}")
