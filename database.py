import os
from flask import Flask
from flask_pymongo import PyMongo
from datetime import datetime as dt

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/myDatabase")
mongo = PyMongo(app)


class myDatabase:
    @staticmethod
    def ensure_indexes():
        """Ensure compound indexes for optimized filtering and export queries."""
        try:
            mongo.db.inventory.create_index([("status", 1), ("priority", 1)])
            mongo.db.inventory.create_index([("datetime", 1)])
        except Exception:
            pass

    @staticmethod
    def addData(title, description, datetime, priority="medium", status="Pending"):
        myDatabase.ensure_indexes()
        mongo.db.inventory.insert_one({
            "title": f"{title}",
            "description": f"{description}",
            "datetime": f"{datetime}",
            "priority": f"{priority}",
            "status": f"{status}"
        })

    @staticmethod
    def findData(datetime):
        projection = {"_id": 0, "title": 1, "description": 1, "datetime": 1, "priority": 1, "status": 1}
        result = mongo.db.inventory.find_one({"datetime": datetime}, projection)
        return result

    @staticmethod
    def showData(priority=None):
        query = {}
        if priority and isinstance(priority, str):
            normalized = priority.strip().lower()
            if normalized in {"low", "medium", "high"}:
                query["priority"] = normalized

        projection = {"_id": 0, "title": 1, "description": 1, "datetime": 1, "priority": 1, "status": 1}
        result = mongo.db.inventory.find(query, projection)
        return result

    @staticmethod
    def get_completed_tasks():
        """Query historical completed tasks (status='Done' or 'completed')."""
        query = {"status": {"$in": ["Done", "completed", "done", "Completed"]}}
        projection = {"_id": 0, "title": 1, "status": 1, "priority": 1, "description": 1, "datetime": 1}
        result = mongo.db.inventory.find(query, projection)
        return list(result)

    @staticmethod
    def updateData(title, description, datetime, priority=None, status=None):
        update_fields = {
            "title": title,
            "description": description,
            "datetime": dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if priority:
            update_fields["priority"] = priority
        if status:
            update_fields["status"] = status

        mongo.db.inventory.update_one({"datetime": datetime}, {"$set": update_fields})

    @staticmethod
    def deleteData(datetime):
        data = {"datetime": datetime}
        mongo.db.inventory.delete_one(data)
