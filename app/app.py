import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

# Connection string comes ONLY from the environment (no hard-coding)
client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=2000)
col = client.get_default_database(default="emidb")["calculations"]

POD_NAME = os.environ.get("HOSTNAME", "unknown")
try:
    POD_IP = socket.gethostbyname(socket.gethostname())
except OSError:
    POD_IP = "unknown"


def positive(value):
    x = float(value)
    if x <= 0 or x != x:  # reject zero, negative and NaN
        raise ValueError
    return x


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/emi", methods=["POST"])
def emi():
    data = request.get_json(silent=True) or request.form
    try:
        p = positive(data.get("principal"))
        rate = positive(data.get("rate"))
        n = int(positive(data.get("months")))
        if n < 1:
            raise ValueError
        r = rate / 12 / 100
        f = (1 + r) ** n
        monthly = p * r * f / (f - 1)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return jsonify(error="Enter positive numbers only"), 400

    total = monthly * n
    doc = {
        "principal": p,
        "rate": rate,
        "months": n,
        "emi": round(monthly, 2),
        "servedBy": POD_NAME,
        "createdAt": datetime.now(timezone.utc),
    }
    try:
        col.insert_one(doc)
    except PyMongoError:
        return jsonify(error="Database unavailable"), 503

    return jsonify(
        emi=round(monthly, 2),
        totalPayment=round(total, 2),
        totalInterest=round(total - p, 2),
        podName=POD_NAME,
        podIp=POD_IP,
    )


@app.route("/api/history")
def history():
    try:
        rows = list(col.find({}, {"_id": 0}).sort("createdAt", -1).limit(10))
    except PyMongoError:
        return jsonify(error="Database unavailable"), 503
    for row in rows:
        row["createdAt"] = row["createdAt"].isoformat()
    return jsonify(rows)


@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return "ok", 200
    except PyMongoError:
        return "mongo unreachable", 503
