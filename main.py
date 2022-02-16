from pymongo import MongoClient
from fastapi import FastAPI

from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()

client = MongoClient("localhost", 27017)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]
estimate_collection = database["estimate"]

# Store the boat's status in variables for quicker access.
where: int
passed: int


class BoatStatus(BaseModel):
    where: int = Field(..., gt=-1, lt=2)  # 0: start, 1: end
    passed: int = Field(..., gt=0, lt=3)  # 1: laser 1, 2: laser 2


class Schedule(BaseModel):
    day_name: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    time: int = Field(..., gt=-1)  # Store this in minutes.


class TimeEstimate(BaseModel):
    t: int = Field(..., gt=-1)  # In minutes.


@app.get("/get-status")
def get_boat_status():
    """Return the boat's status."""
    return {"where": where,
            "passed": passed}


@app.post("/update-status")
def update_boat_status(boat_status: BoatStatus):
    """Update the boat's status."""
    global where, passed
    where = boat_status.where
    passed = boat_status.passed
    return {"status": "Boat status updated!",
            "where": where,
            "passed": passed}


@app.get("/get-schedule")
def get_schedule():
    """Return all schedules."""
    result_raw = schedule_collection.find({}, {"_id": 0})
    result_list = []
    for result in result_raw:
        result_list.append(result)
    return {"schedules": result_list}


@app.post("/create-schedule")
def create_schedule(schedule: Schedule):
    """Create a new schedule. If the schedule already exists, return an error."""
    if schedule_collection.find_one({"day_name": schedule.day_name, "time": schedule.time}) is not None:
        return {"status": "Schedule already exists!"}
    schedule_collection.insert_one(schedule.dict())
    return {"status": "Schedule created!",
            "day_name": schedule.day_name,
            "time": schedule.time}


@app.post("/delete-schedule")
def delete_schedule(schedule: Schedule):
    """Delete a schedule."""
    if schedule_collection.find_one({"day_name": schedule.day_name, "time": schedule.time}) is None:
        return {"status": "Schedule does not exist!"}
    schedule_collection.delete_one({"day_name": schedule.day_name, "time": schedule.time})
    return {"status": "Schedule deleted!",
            "day_name": schedule.day_name,
            "time": schedule.time}


@app.post("/time-estimation")
def time_estimation(request: TimeEstimate):
    """Write time to database, and return the estimated time."""
    estimate_data = {"estimate_time": 0,  # Document template.
                     "count": 0}

    if estimate_collection.find_one() is None:
        # If there is no record of estimated time in the database, create one.
        estimate_data["estimate_time"] = request.t
        estimate_data["count"] = 1
        estimate_collection.insert_one(estimate_data)
    else:
        # If there is a record of estimated time in the database, update it.
        old_est_time = estimate_collection.find_one()["estimate_time"]
        new_count = estimate_collection.find_one()["count"] + 1
        estimate_data["estimate_time"] = (old_est_time *
                                          new_count + request.t) / (new_count + 1)
        estimate_data["count"] = new_count
        estimate_collection.update_one({}, {"$set": estimate_data})
    # Return the estimated time.
    return {"status": "Estimated time updated!",
            "estimated_time": estimate_collection.find_one({}, {"_id": 0})}
