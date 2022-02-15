from pymongo import MongoClient
from fastapi import FastAPI

from pydantic import BaseModel, Field

from datetime import datetime

app = FastAPI()

client = MongoClient("localhost", 27017)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]


class BoatStatus(BaseModel):
    where: int = Field(..., gt=-1, lt=2)  # 0: start, 1: end
    passed: int = Field(..., gt=0, lt=3)  # 1: laser 1, 2: laser 2


@app.get("/get-status")
def get_boat_status():
    return boat_status_collection.find_one({}, {"_id": 0})


@app.post("/update-status")
def update_boat_status(boat_status: BoatStatus):
    boat_status_collection.update_one({}, {"$set": boat_status.dict()}, upsert=True)
    return {"status": "Boat status updated!",
            "where": boat_status.where,
            "passed": boat_status.passed}
