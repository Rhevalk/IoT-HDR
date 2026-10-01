from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mqtt.consumer import fast_mqtt
from db.database import init_db

app = FastAPI(title="IoT MQTT Gateway")

# 1. Setup CORS (Penting agar Streamlit bisa akses API ini)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Bisa dipersempit ke port Streamlit nanti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Inisialisasi MQTT
fast_mqtt.init_app(app)

# 3. Inisialisasi DB
init_db()

@app.get("/")
async def root():
    return {"status": "online", "message": "IoT Backend API Gateway"}
