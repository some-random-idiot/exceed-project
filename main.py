from pymongo import MongoClient
from fastapi import FastAPI

from pydantic import BaseModel

from datetime import datetime

app = FastAPI()

client = MongoClient("localhost", 27017)

database = client["project"]
boat_status_collection = database["boat_status"]
schedule_collection = database["schedule"]
