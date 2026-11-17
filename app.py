import io
import csv
from flask import Flask, render_template, request, redirect, Response
from database import myDatabase
from datetime import datetime as dt

app = Flask(__name__)

ALLOWED_PRIORITIES = {"low", "medium", "high"}
DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def normalize_priority(raw_priority):
    """Normalize priority string with default fallback to 'medium'."""
    if not raw_priority or not isinstance(raw_priority, str):
        return "medium"
    cleaned = raw_priority.strip().lower()
    return cleaned if cleaned in ALLOWED_PRIORITIES else "medium"


def sanitize_csv_cell(value):
    """
    Sanitize CSV field to prevent OWASP CSV formula injection attacks.
    If the value starts with dangerous control characters (=, +, -, @, \\t, \\r),
    prepend a single quotation mark (').
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val.startswith(DANGEROUS_FORMULA_PREFIXES):
        return f"'{str_val}"
    return str_val


def generate_completed_tasks_csv_response():
    """Helper to generate RFC 4180 CSV response for completed tasks."""
    completed_tasks = myDatabase.get_completed_tasks()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")

    # Header row
    writer.writerow(["Title", "Status", "Priority"])

    for task in completed_tasks:
        raw_title = task.get("title", "")
        raw_status = task.get("status", "Done")
        raw_priority = normalize_priority(task.get("priority"))

        sanitized_title = sanitize_csv_cell(raw_title)
        sanitized_status = sanitize_csv_cell(raw_status)
        sanitized_priority = sanitize_csv_cell(raw_priority)

        writer.writerow([sanitized_title, sanitized_status, sanitized_priority])

    csv_data = output.getvalue()
    output.close()

    response = Response(csv_data, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=completed_tasks.csv"
    return response


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = normalize_priority(request.form.get("priority"))
        datetime = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        myDatabase.addData(title, description, datetime, priority=priority)
        return redirect("/")

    else:
        raw_priority = request.args.get("priority")
        filter_priority = None
        if raw_priority and isinstance(raw_priority, str):
            normalized = raw_priority.strip().lower()
            if normalized in ALLOWED_PRIORITIES:
                filter_priority = normalized

        allData = list(myDatabase.showData(priority=filter_priority))
        return render_template("index.html", allToDo=allData)


@app.route("/tasks/completed/export", methods=["GET"])
@app.route("/export/completed/csv", methods=["GET"])
def export_completed_csv():
    """
    Export completed tasks in RFC 4180 CSV format with formula injection sanitization.
    Available at /tasks/completed/export (ARCH-8188) and /export/completed/csv.
    """
    return generate_completed_tasks_csv_response()


@app.route("/update/<string:datetime>", methods=["GET", "POST"])
def update(datetime):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        raw_priority = request.form.get("priority")
        priority = normalize_priority(raw_priority) if raw_priority else None
        myDatabase.updateData(title, description, datetime, priority=priority)
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
