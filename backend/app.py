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
@app.route("/recognize", methods=["POST"])
def recognize():

    try:

        if not os.path.exists(RECOGNIZE_FILE):

            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "recognize.py not found."
            }), 404

        trainer_file = os.path.join(
            MODEL_DIR,
            "trainer.yml"
        )

        labels_file = os.path.join(
            MODEL_DIR,
            "labels.pkl"
        )

        if not os.path.exists(trainer_file):

            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "trainer.yml not found. Train the model first."
            }), 400

        if not os.path.exists(labels_file):

            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "labels.pkl not found. Train the model first."
            }), 400

        result = subprocess.run(
            [
                sys.executable,
                RECOGNIZE_FILE
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:

            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "Face recognition failed.",
                "error": result.stderr,
                "output": result.stdout
            }), 500

        output = result.stdout.strip()

        return jsonify({
            "status": "success",
            "recognized": True,
            "message": "Face recognition completed successfully.",
            "output": output
        })

    except subprocess.TimeoutExpired:

        return jsonify({
            "status": "error",
            "recognized": False,
            "message": "Face recognition timed out."
        }), 500

    except Exception as e:

        return jsonify({
            "status": "error",
            "recognized": False,
            "message": str(e)
        }), 500