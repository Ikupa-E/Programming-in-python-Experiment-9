from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-for-jwt-signing-123456"
API_KEY = "my-api-key-123"
USERS = {"admin": "admin123"}

students = [
    {"id": 1, "name": "Ikupa Ephraim", "branch": "CSE (Cybersecurity)", "cgpa": 8.7},
    {"id": 2, "name": "Aman Singh", "branch": "CSE", "cgpa": 8.1},
    {"id": 3, "name": "Riya Sharma", "branch": "IT", "cgpa": 9.0},
]


def api_key_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-KEY") != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return wrapper


def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Token is missing"}), 401
        token = auth.split(" ", 1)[1]
        try:
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "API is running"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if USERS.get(username) != password or username is None:
        return jsonify({"error": "Invalid credentials"}), 401
    token = jwt.encode(
        {
            "user": username,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({"token": token})


@app.route("/api/students", methods=["GET"])
@api_key_required
def get_students():
    return jsonify(students)


@app.route("/api/students/<int:sid>", methods=["GET"])
@api_key_required
def get_student(sid):
    for s in students:
        if s["id"] == sid:
            return jsonify(s)
    return jsonify({"error": "Student not found"}), 404


@app.route("/api/students", methods=["POST"])
@jwt_required
def add_student():
    data = request.get_json() or {}
    if not all(k in data for k in ("name", "branch", "cgpa")):
        return jsonify({"error": "name, branch and cgpa are required"}), 400
    new_id = max(s["id"] for s in students) + 1 if students else 1
    student = {"id": new_id, "name": data["name"], "branch": data["branch"], "cgpa": data["cgpa"]}
    students.append(student)
    return jsonify(student), 201


@app.route("/api/students/<int:sid>", methods=["PUT"])
@jwt_required
def update_student(sid):
    data = request.get_json() or {}
    for s in students:
        if s["id"] == sid:
            s.update({k: v for k, v in data.items() if k in ("name", "branch", "cgpa")})
            return jsonify(s)
    return jsonify({"error": "Student not found"}), 404


@app.route("/api/students/<int:sid>", methods=["DELETE"])
@jwt_required
def delete_student(sid):
    for s in students:
        if s["id"] == sid:
            students.remove(s)
            return jsonify({"message": "Student deleted"})
    return jsonify({"error": "Student not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)