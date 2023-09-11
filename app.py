from flask import Flask, render_template, request, redirect, url_for
from database import myDatabase
from datetime import datetime as dt

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        datetime = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        myDatabase.addData(title, description, datetime)
        return redirect("/")

    else:
        allData = list(myDatabase.showData())
        return render_template("index.html", allToDo=allData)


@app.route("/update/<string:datetime>", methods=["GET", "POST"])
def update(datetime):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        myDatabase.updateData(title, description, datetime)
        return redirect("/")

    else:
        todo = myDatabase.findData(datetime)
        return render_template("update.html", todo=todo)


@app.route("/delete/<string:datetime>")
def delete(datetime):
    myDatabase.deleteData(datetime)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
