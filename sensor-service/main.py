from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import httpx 



app = FastAPI(title="Gobe IoT API")


client = AsyncIOMotorClient("mongodb://db-sensors:27017") # definiraš bazo
db = client.mushroom_db


@app.get("/")
async def root():
    return {"message": "API teče. Za podatke pojdi na /v1/sensors/latest"}

@app.post("/v1/sensors/data")
async def receive_ttn_data(request: Request):
    payload = await request.json()
    
    # Izpis celotnega paketa za diagnostiko v logs
    print(f"DEBUG PAYLOAD: {payload}")
    
    try:
        # Tle dobivaš senzor podatke iz TTN webhooka
        uplink = payload.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})
        
        temp = decoded.get("temperature")
        hum = decoded.get("humidity")
        device_id = payload.get("end_device_ids", {}).get("device_id", "unknown")

        if temp is None or hum is None:
            print(f"Podatki so None! T={temp}, H={hum}")
            return {"status": "warning", "message": "Missing temperature or humidity"}

        # Formatiraš entry v MongoDB
        document = {
            "device_id": device_id,
            "temperature": float(temp),
            "humidity": float(hum),
            "timestamp": datetime.datetime.utcnow()
        }
        
        # shraniš v bazo
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



USER_SERVICE_URL = "http://user-service:8000"

async def check_proactive_conditions(device_id: str, current_temp: float, current_hum: float):
    """
    Proaktivna logika: Preveri zadnjih 10 dni in sproži obvestilo.
    """
    # iz baze vzamemo podatke zadnjih 10 dni (za spreizkus raje nastavimo na manj in nastavimo IoT device da vsakih npr. 2 minute fila podatke v bazo)
    ten_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=10)
    cursor = db.readings.find({
        "device_id": device_id,
        "timestamp": {"$gte": ten_days_ago}
    })
    history = await cursor.to_list(length=1000)
    
    if not history:
        return

    # Logika je zaenkrat bolj simple samo kot proof of concept
    # Izračunamo povprečno vlago zadnjih 10 dni
    avg_hum = sum(d['humidity'] for d in history) / len(history)
    
    # Pogoj: Če je povprečna vlaga visoka IN trenutna temperatura idealna (15-20°C) ampak senzor meri direktno ob čipu -> ga greje za ene 10 stopinj zamaknjeno
    if avg_hum > 75 and 30 <= current_temp <= 35:
        print(f"!!! OPTIMALNI POGOJI ZA {device_id} !!!")
        
        # 3. Poiščemo lastnika naprave preko User Service-a
        async with httpx.AsyncClient() as client:
            try:
                # Pokličemo TVOJ internal endpoint v user-service
                response = await client.get(f"{USER_SERVICE_URL}/internal/device-owner/{device_id}")
                
                if response.status_code == 200:
                    user_data = response.json()
                    # Zdaj ko imaš user_data, lahko dejansko simuliraš obvestilo
                    print(f">>> PROAKTIVNO OPOZORILO POSLANO: {user_data['email']} <<<")
                    print(f"Uporabnik {user_data['username']}, gobe na lokaciji {device_id} so pripravljene!")
                else:
                    print(f"Naprava {device_id} nima registriranega lastnika v User Service.")
            except Exception as e:
                print(f"Napaka pri povezovanju z User Service: {e}")

@app.post("/v1/sensors/data")
async def receive_ttn_data(request: Request):
    payload = await request.json()
    try:
        uplink = payload.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})
        temp = decoded.get("temperature")
        hum = decoded.get("humidity")
        device_id = payload.get("end_device_ids", {}).get("device_id", "unknown")

        if temp is not None and hum is not None:
            document = {
                "device_id": device_id,
                "temperature": float(temp),
                "humidity": float(hum),
                "timestamp": datetime.datetime.utcnow()
            }
            await db.readings.insert_one(document)
            
            #Sproži analizo brez čakanja 
            await check_proactive_conditions(device_id, float(temp), float(hum))
            
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}