from fastapi import FastAPI, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import httpx 

app = FastAPI(title="Gobe IoT API")

# Povezava na MongoDB
client = AsyncIOMotorClient("mongodb://db-sensors:27017")
db = client.mushroom_db # Uporabljamo tvoje ime baze

@app.on_event("startup")
async def create_indexes():
    # POMEMBNO: Uporabljamo db.readings, ker tam shranjuješ podatke!
    # Ustvari indeks na device_id in timestamp (padajoče)
    await db.readings.create_index([("device_id", 1), ("timestamp", -1)])
    print("Indeksi na db.readings so bili uspešno ustvarjeni!")

@app.get("/")
async def root():
    return {"message": "API teče. Za podatke pojdi na /v1/sensors/latest"}

# --- POMOŽNA FUNKCIJA ZA ANALITIKO ---
USER_SERVICE_URL = "http://user-service:8000"

async def check_proactive_conditions(device_id: str, current_temp: float, current_hum: float):
    """
    Proaktivna logika: Preveri pogoje in kontaktira User Service za obveščanje.
    """
    # Vzamemo podatke zadnjih 10 dni
    ten_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=10)
    cursor = db.readings.find({
        "device_id": device_id,
        "timestamp": {"$gte": ten_days_ago}
    })
    history = await cursor.to_list(length=1000)
    
    if not history:
        return

    # Izračunamo povprečno vlago
    avg_hum = sum(d['humidity'] for d in history) / len(history)
    
    # Tvoj specifičen pogoj za gobe (z upoštevanjem segrevanja čipa)
    if avg_hum > 75 and 30 <= current_temp <= 35:
        print(f"!!! OPTIMALNI POGOJI ZA {device_id} !!!")
        
        async with httpx.AsyncClient() as client:
            try:
                # Pokličemo internal endpoint v user-service
                response = await client.get(f"{USER_SERVICE_URL}/internal/device-owner/{device_id}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    print(f">>> PROAKTIVNO OPOZORILO POSLANO: {user_data['email']} <<<")
                else:
                    print(f"Naprava {device_id} nima lastnika.")
            except Exception as e:
                print(f"Napaka pri povezovanju z User Service: {e}")

# --- ENDPOINTI ---

@app.post("/v1/sensors/data")
async def receive_ttn_data(request: Request):
    payload = await request.json()
    
    # Debug izpis v loge
    print(f"DEBUG PAYLOAD: {payload}")
    
    try:
        uplink = payload.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})
        
        temp = decoded.get("temperature")
        hum = decoded.get("humidity")
        device_id = payload.get("end_device_ids", {}).get("device_id", "unknown")

        if temp is None or hum is None:
            return {"status": "warning", "message": "Missing temperature or humidity"}

        # Priprava dokumenta s časovnim žigom
        document = {
            "device_id": device_id,
            "temperature": float(temp),
            "humidity": float(hum),
            "timestamp": datetime.datetime.utcnow()
        }
        
        # Shranjevanje v MongoDB (kolekcija 'readings')
        result = await db.readings.insert_one(document)
        
        # Sproži analizo (proaktivno obveščanje)
        await check_proactive_conditions(device_id, float(temp), float(hum))
        
        return {"status": "success", "db_id": str(result.inserted_id)}

    except Exception as e:
        print(f"Napaka: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/v1/sensors/{device_id}/latest")
async def get_latest_data(device_id: str, limit: int = 20):
    # Uporabimo indeks za hitro pridobivanje zadnjih N zapisov
    cursor = db.readings.find({"device_id": device_id}).sort("timestamp", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results