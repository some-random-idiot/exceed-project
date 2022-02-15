from pymongo import MongoClient
from fastapi import FastAPI

from pydantic import BaseModel, Field
from typing import Literal, Dict

app = FastAPI()

client = MongoClient("localhost", 27017)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]
estimate_collection = database["estimate"]


class BoatStatus(BaseModel):
    where: int = Field(..., gt=-1, lt=2)  # 0: start, 1: end
    passed: int = Field(..., gt=0, lt=3)  # 1: laser 1, 2: laser 2


class Schedule(BaseModel):
    day_name: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    time: int  # Store this in minutes.


@app.get("/get-status")
def get_boat_status():
    return boat_status_collection.find_one({}, {"_id": 0})


@app.post("/update-status")
def update_boat_status(boat_status: BoatStatus):
    boat_status = boat_status.dict()
    boat_status_collection.update_one({}, {"$set": boat_status}, upsert=True)
    return {"status": "Boat status updated!",
            "where": boat_status["where"],
            "passed": boat_status["passed"]}


@app.get("/get-schedule")
def get_schedule():
    return schedule_collection.find({}, {"_id": 0})


@app.post("/create-schedule")
def create_schedule(schedule: Schedule):
    schedule_collection.insert_one(schedule.dict())
    return {"status": "Schedule updated!",
            "day_name": schedule.day_name,
            "time": schedule.time}


@app.post("/estimate-time")
def estimate_time(request: Dict[Literal['t'], int]):
    estimate_data = {"estimate_time": 0,
                     "count": 0}
    if estimate_collection.find_one() is None:
        estimate_data["estimate_time"] = request['t']
        estimate_data["count"] = 1
        estimate_collection.insert_one(estimate_data)
    else:
        estimate_data["estimate_time"] = (estimate_data["estimate_time"] * estimate_data["count"] + request['t']) \
                                         / (estimate_data["count"] + 1)
        estimate_data["count"] = estimate_collection.find_one()["count"] + 1
        estimate_collection.update_one({}, {"$set": estimate_data})
    return {"status": "Estimated time updated!",
            "estimated_time": estimate_collection.find_one()}
