from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime = datetime.utcnow()

    class Config:
        schema_extra = {
            "example": {
                "sensor_id": "lht65-12345",
                "temperature": 22.5,
                "humidity": 60.0
            }
        }