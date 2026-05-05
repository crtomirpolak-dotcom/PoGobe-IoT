from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
import datetime

# 1. NAJPREJ definiramo app
app = FastAPI(title="Gobe IoT API")

# 2. POTEM nastavimo bazo
client = AsyncIOMotorClient("mongodb://db-sensors:27017")
db = client.mushroom_db

# 3. NA KONCU dodamo poti (endpoints)
@app.get("/")
async def root():
    return {"message": "API teče. Za podatke pojdi na /v1/sensors/latest"}

@app.post("/v1/sensors/data")
async def receive_ttn_data(request: Request):
    payload = await request.json()
    
    # Izpis celotnega paketa za diagnostiko v logs
    print(f"DEBUG PAYLOAD: {payload}")
    
    try:
        # Pridobivanje podatkov iz TTN strukture (glede na tvoj zadnji log)
        uplink = payload.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})
        
        temp = decoded.get("temperature")
        hum = decoded.get("humidity")
        device_id = payload.get("end_device_ids", {}).get("device_id", "unknown")

        if temp is None or hum is None:
            print(f"Podatki so None! T={temp}, H={hum}")
            return {"status": "warning", "message": "Missing temperature or humidity"}

        # Priprava dokumenta za MongoDB
        document = {
            "device_id": device_id,
            "temperature": float(temp),
            "humidity": float(hum),
            "timestamp": datetime.datetime.utcnow()
        }
        
        # Shranjevanje v bazo
        result = await db.readings.insert_one(document)
        print(f"USPEH! Shranjeno: {device_id} | T: {temp}°C, H: {hum}%")
        
        return {"status": "success", "db_id": str(result.inserted_id)}

    except Exception as e:
        print(f"Napaka pri obdelavi: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/v1/sensors/latest")
async def get_latest_data():
    cursor = db.readings.find().sort("timestamp", -1).limit(10)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results