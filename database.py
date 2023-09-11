from flask import Flask, render_template
from flask_pymongo import PyMongo
from datetime import datetime as dt

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app)


class myDatabase:
    @staticmethod
    def addData(title, description, datetime):
        mongo.db.inventory.insert_one({
            "title": f"{title}",
            "description": f"{description}",
            "datetime": f"{datetime}"
        })

    @staticmethod
    def findData(datetime):
        result = mongo.db.inventory.find_one({"datetime": datetime}, {
                                             "_id": 0, "title": 1, "description": 1, "datetime": 1})
        return result

    @staticmethod
    def showData():
        result = mongo.db.inventory.find(
            {}, {"_id": 0, "title": 1, "description": 1, "datetime": 1})
        return result

    @staticmethod
    def updateData(title, description, datetime):
        data = {"datetime": datetime}
        mongo.db.inventory.update_one({"datetime": datetime},
                                      {"$set": {"title": title, "description": description, "datetime": dt.now().strftime("%Y-%m-%d %H:%M:%S")}})

    @staticmethod
    def deleteData(datetime):
        data = {"datetime": datetime}
        mongo.db.inventory.delete_one(data)
