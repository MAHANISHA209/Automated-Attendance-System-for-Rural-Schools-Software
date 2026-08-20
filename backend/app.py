from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import sys
import csv
from datetime import datetime


app = Flask(__name__)
CORS(app)


# ==========================================
# DIRECTORIES
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")

TRAIN_FILE = os.path.join(BASE_DIR, "train.py")
RECOGNIZE_FILE = os.path.join(BASE_DIR, "recognize.py")

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "Attendance.csv"
)


os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# ==========================================
# HOME
# ==========================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "Face Recognition API is running successfully!"
    })


# ==========================================
# REGISTER STUDENT
# ==========================================

@app.route("/register", methods=["POST"])
def register():

    try:

        student_name = request.form.get(
            "student_name",
            ""
        ).strip()


        if not student_name:

            return jsonify({
                "status": "error",
                "message": "Student name is required."
            }), 400


        student_dir = os.path.join(
            DATASET_DIR,
            student_name
        )


        os.makedirs(
            student_dir,
            exist_ok=True
        )


        images = request.files.getlist(
            "images"
        )


        if not images:

            return jsonify({
                "status": "error",
                "message": "No images received."
            }), 400


        saved = 0


        for image in images:

            if not image.filename:
                continue


            filename = f"{saved + 1}.jpg"


            filepath = os.path.join(
                student_dir,
                filename
            )


            image.save(filepath)

            saved += 1


        return jsonify({

            "status": "success",

            "message":
                "Registration completed successfully.",

            "student_name":
                student_name,

            "images_saved":
                saved

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# ==========================================
# TRAIN FACE MODEL
# ==========================================

@app.route("/train", methods=["GET", "POST"])
def train():

    try:

        if not os.path.exists(TRAIN_FILE):

            return jsonify({

                "status": "error",

                "message":
                    "train.py not found."

            }), 404


        result = subprocess.run(

            [
                sys.executable,
                TRAIN_FILE
            ],

            cwd=BASE_DIR,

            capture_output=True,

            text=True
        )


        if result.returncode != 0:

            return jsonify({

                "status": "error",

                "message":
                    "Face training failed.",

                "error":
                    result.stderr,

                "output":
                    result.stdout

            }), 500


        return jsonify({

            "status": "success",

            "message":
                "Face training completed successfully.",

            "output":
                result.stdout

        })


    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# ==========================================
# FACE RECOGNITION
# ==========================================

# ==========================================
# VIEW ATTENDANCE
# PRESENT / ABSENT
# ==========================================
# ==========================================
# VIEW ATTENDANCE
# PRESENT / ABSENT
# ==========================================

@app.route("/attendance", methods=["GET"])
def attendance():

    try:

        today = datetime.now().strftime("%Y-%m-%d")

        students = []

        if os.path.exists(DATASET_DIR):

            for name in os.listdir(DATASET_DIR):

                student_path = os.path.join(
                    DATASET_DIR,
                    name
                )

                if os.path.isdir(student_path):
                    students.append(name)

        present_students = {}

        if os.path.exists(ATTENDANCE_FILE):

            with open(
                ATTENDANCE_FILE,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    student_name = (
                        row.get("Student Name")
                        or row.get("student_name")
                        or ""
                    ).strip()

                    date = (
                        row.get("Date")
                        or row.get("date")
                        or ""
                    ).strip()

                    time = (
                        row.get("Time")
                        or row.get("time")
                        or ""
                    ).strip()

                    if student_name and date == today:
                        present_students[student_name] = time

        records = []

        for student in sorted(students):

            if student in present_students:

                records.append({
                    "Student Name": student,
                    "Date": today,
                    "Time": present_students[student],
                    "Status": "Present"
                })

            else:

                records.append({
                    "Student Name": student,
                    "Date": today,
                    "Time": "--",
                    "Status": "Absent"
                })

        return jsonify({
            "status": "success",
            "records": records
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500