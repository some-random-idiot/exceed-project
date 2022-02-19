from typing import Literal, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient

from datetime import datetime

started = 0

app = FastAPI()

client = MongoClient("localhost", 27017)
trusted_origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]
estimate_collection = database["estimate"]


class BoatStatus(BaseModel):
    where: Optional[int]
    passed: Optional[int]
    start_time: Optional[int]


class Schedule(BaseModel):
    day_name: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    time: int = Field(..., gt=-1)  # Store this in minutes.


class ScheduleEdit(Schedule):
    old_day_name: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    old_time: int = Field(..., gt=-1)  # Store this in minutes.


class TimeEstimate(BaseModel):
    t: int = Field(..., gt=-2)  # In minutes.


@app.get("/start-boat")
def start_boat(start: int = None):
    """Set the start value for activating/deactivating the boat."""
    global started

    # Memorize the start time in seconds.
    if start == 1 and started == 0:
        if boat_status_collection.find_one() is None:
            # If the boat status is not found, create a new one.
            boat_status_collection.insert_one({"where": 0, "passed": -1})
        # Store the start time in seconds.
        start_time = datetime.now().hour * 3600 + datetime.now().minute * 60 + datetime.now().second
        boat_status_collection.update_one({}, {"$set": {"start_time": start_time}})

    if start in [0, 1]:
        started = start
    elif start is not None:
        raise HTTPException(422, "Invalid 'start' value! It can only be 0 or 1.")

    return {"status": started}


@app.get("/get-status")
def get_boat_status():
    """Return the boat's status."""
    if boat_status_collection.find_one() is None:
        raise HTTPException(404, "Boat status not found!")
    return boat_status_collection.find_one({}, {"_id": 0})


@app.post("/update-status")
def update_boat_status(boat_status: BoatStatus):
    """Update the boat's status."""
    boat_status = boat_status.dict()  # Convert to dict.

    if boat_status["start_time"] is not None:
        # If the start time is not None, then record the starting time.
        boat_status_collection.update_one({}, {"$set": {"start_time": boat_status["start_time"]}})
    else:
        if boat_status["where"] not in [-1, 0, 1] and boat_status["where"] is not None:
            # Check if the 'where' attribute is valid.
            raise HTTPException(422, "Invalid 'where' value!")
        elif boat_status["passed"] not in [0, 1, 2, 3] and boat_status["passed"] is not None:
            # Check if the 'passed' attribute is valid.
            return HTTPException(422, "Invalid 'passed' value!")
        elif boat_status["where"] in [-1, 0, 1] or boat_status["passed"] in [0, 1, 2, 3]:
            # Update the boat status.
            if boat_status["where"] in [-1, 0, 1] and boat_status["passed"] is None:
                # If only 'where' attribute is provided, update the 'where' attribute.
                boat_status_collection.update_one({}, {"$set": {"where": boat_status["where"]}}, upsert=True)
                return {"status": "Boat status updated!",
                        "where": boat_status["where"]}
            elif boat_status["where"] is None and boat_status["passed"] in [0, 1, 2, 3]:
                # If only 'passed' attribute is provided, update the 'passed' attribute.
                boat_status_collection.update_one({}, {"$set": {"passed": boat_status["passed"]}}, upsert=True)
                return {"status": "Boat status updated!",
                        "passed": boat_status["passed"]}
        else:
            raise HTTPException(422, "Unexpected request body!")


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
        raise HTTPException(422, "Schedule already exists!")
    schedule_collection.insert_one(schedule.dict())
    return {"status": "Schedule created!",
            "day_name": schedule.day_name,
            "time": schedule.time}


@app.put("/edit-schedule")
async def edit_schedule(schedule: Request):
    """Delete the old schedule and create a new one. If the new schedule information already exists, return an error."""
    schedule = await schedule.json()

    try:
        if schedule_collection.find_one({"day_name": schedule["old_day_name"], "time": schedule["old_time"]}) is None:
            raise HTTPException(404, "The schedule targeted for change does not exist!")
        if schedule_collection.find_one({"day_name": schedule["day_name"], "time": schedule["time"]}) is not None:
            raise HTTPException(422, "The provided new schedule combination already exists!")
        else:
            new_schedule = {"day_name": schedule["day_name"], "time": schedule["time"]}
            schedule_collection.delete_one({"day_name": schedule["old_day_name"], "time": schedule["old_time"]})
            schedule_collection.insert_one(new_schedule)
            return {"status": "Schedule edited!",
                    "day_name": schedule["day_name"],
                    "time": schedule["time"],
                    "old_day_name": schedule["old_day_name"],
                    "old_time": schedule["old_time"]}
    except KeyError:
        raise HTTPException(422, "Unexpected request body!")


@app.delete("/delete-schedule")
def delete_schedule(schedule: Schedule):
    """Delete a schedule."""
    if schedule_collection.find_one({"day_name": schedule.day_name, "time": schedule.time}) is None:
        raise HTTPException(404, "Schedule does not exist!")
    schedule_collection.delete_one({"day_name": schedule.day_name, "time": schedule.time})
    return {"status": "Schedule deleted!",
            "day_name": schedule.day_name,
            "time": schedule.time}


@app.get("/get-time-estimate")
def get_time_estimate():
    """Return the estimated time."""
    result = estimate_collection.find_one({}, {"_id": 0})
    if result is not None:
        return {"estimate_time": result["estimate_time"]}
    else:
        raise HTTPException(404, "No estimation data available!")


@app.post("/update-time-estimate")
def update_time_estimate(request: TimeEstimate):
    """Receive a time, calculate the estimated time from it, then record the estimated time to the database.
    If t = -1 then reset 'estimated_time' and 'count'."""
    estimate_data = {"estimate_time": 0,  # Document template.
                     "count": 0}

    if estimate_collection.find_one() is None:
        # If there is no record of estimated time in the database, create one.
        estimate_collection.insert_one(estimate_data)

    if request.t == -1:
        # If t = -1, reset 'estimated_time' and 'count'.
        estimate_collection.update_one({}, {"$set": estimate_data})
        return {"status": "Estimated time has been reset!"}
    else:
        # If there is a record of estimated time in the database, update it.
        old_est_time = estimate_collection.find_one()["estimate_time"]
        old_count = estimate_collection.find_one()["count"]
        estimate_data["estimate_time"] = (old_est_time * old_count + request.t) / (old_count + 1)
        estimate_data["count"] = old_count + 1
        estimate_collection.update_one({}, {"$set": estimate_data})

    # Return the estimated time.
    return {"status": "Estimated time updated!",
            "data": estimate_collection.find_one({}, {"_id": 0})}
