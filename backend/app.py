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
        import cv2
        import pickle

        # -----------------------------
        # Check image received
        # -----------------------------

        if "image" not in request.files:
            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "No image received."
            }), 400

        image_file = request.files["image"]

        if not image_file.filename:
            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "Invalid image."
            }), 400

        # -----------------------------
        # Load image
        # -----------------------------

        image_bytes = image_file.read()

        import numpy as np

        image_array = np.frombuffer(
            image_bytes,
            np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "Could not read image."
            }), 400

        # -----------------------------
        # Load model
        # -----------------------------

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
                "message": "trainer.yml not found."
            }), 400

        if not os.path.exists(labels_file):
            return jsonify({
                "status": "error",
                "recognized": False,
                "message": "labels.pkl not found."
            }), 400

        recognizer = cv2.face.LBPHFaceRecognizer_create()

        recognizer.read(trainer_file)

        with open(labels_file, "rb") as file:
            label_map = pickle.load(file)

        # -----------------------------
        # Face detector
        # -----------------------------

        face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            "haarcascade_frontalface_default.xml"
        )

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )

        # -----------------------------
        # No face
        # -----------------------------

        if len(faces) == 0:

            return jsonify({
                "status": "success",
                "recognized": False,
                "message": "No face detected. Attendance not marked."
            })

        # -----------------------------
        # Recognize face
        # -----------------------------

        for (x, y, w, h) in faces:

            face = gray[
                y:y+h,
                x:x+w
            ]

            face = cv2.resize(
                face,
                (200, 200)
            )

            student_id, confidence = recognizer.predict(
                face
            )

            print(
                "Predicted ID:",
                student_id,
                "Confidence:",
                confidence
            )

            # Lower confidence = better match

            if confidence < 70:

                student_name = label_map.get(
                    student_id
                )

                if not student_name:
                    continue

                # -----------------------------
                # Mark attendance
                # -----------------------------

                today = datetime.now().strftime(
                    "%Y-%m-%d"
                )

                current_time = datetime.now().strftime(
                    "%H:%M:%S"
                )

                already_marked = False

                if os.path.exists(ATTENDANCE_FILE):

                    with open(
                        ATTENDANCE_FILE,
                        "r",
                        newline="",
                        encoding="utf-8-sig"
                    ) as file:

                        reader = csv.DictReader(file)

                        for row in reader:

                            row_name = (
                                row.get("Student Name")
                                or ""
                            ).strip()

                            row_date = (
                                row.get("Date")
                                or ""
                            ).strip()

                            if (
                                row_name == student_name
                                and row_date == today
                            ):

                                already_marked = True
                                break

                if not already_marked:

                    with open(
                        ATTENDANCE_FILE,
                        "a",
                        newline="",
                        encoding="utf-8"
                    ) as file:

                        writer = csv.writer(file)

                        writer.writerow([
                            student_name,
                            today,
                            current_time,
                            "Present"
                        ])

                    message = (
                        student_name +
                        " recognized. Attendance marked Present."
                    )

                else:

                    message = (
                        student_name +
                        " already marked Present today."
                    )

                return jsonify({
                    "status": "success",
                    "recognized": True,
                    "student_name": student_name,
                    "message": message
                })

        # -----------------------------
        # Face detected but unknown
        # -----------------------------

        return jsonify({
            "status": "success",
            "recognized": False,
            "message": "Face detected but student was not recognized. Attendance not marked."
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "recognized": False,
            "message": str(e)
        }), 500