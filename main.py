from pymongo import MongoClient
from fastapi import FastAPI

from pydantic import BaseModel

from datetime import datetime

app = FastAPI()

client = MongoClient("localhost", 27017)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]


class BoatStatus(BaseModel):
    where: int  # 0: start, 1: end
    passed: int  # 1: laser 1, 2: laser 2


@app.post("/update-boat-status")
def update_boat_status(boat_status: BoatStatus):
    boat_status_collection.insert_one(boat_status.dict())
    return {"status": "Boat status updated!"}
