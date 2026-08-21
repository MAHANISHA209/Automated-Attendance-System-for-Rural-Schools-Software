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
# MARK ATTENDANCE
# ==========================================

def mark_attendance(student_name):

    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    # Create CSV if it does not exist
    if not os.path.exists(ATTENDANCE_FILE):

        with open(
            ATTENDANCE_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Student Name",
                "Date",
                "Time",
                "Status"
            ])

    # Check whether already marked today
    with open(
        ATTENDANCE_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if (
                row.get("Student Name") == student_name
                and row.get("Date") == today
            ):

                return False

    # Add attendance
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

    return True


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

@app.route("/recognize", methods=["POST"])
def recognize():

    temp_image = os.path.join(
        BASE_DIR,
        "temp_face.jpg"
    )

    try:

        # -------------------------------
        # Receive browser camera image
        # -------------------------------

        image = request.files.get("image")

        if image is None:

            return jsonify({
                "status": "error",
                "recognized": False,
                "message":
                    "No camera image received."
            }), 400


        # -------------------------------
        # Check model
        # -------------------------------

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
                "message":
                    "trainer.yml not found."
            }), 400


        if not os.path.exists(labels_file):

            return jsonify({
                "status": "error",
                "recognized": False,
                "message":
                    "labels.pkl not found."
            }), 400


        # -------------------------------
        # Save browser image
        # -------------------------------

        image.save(temp_image)


        # -------------------------------
        # Run recognition
        # -------------------------------

        result = subprocess.run(

            [
                sys.executable,
                RECOGNIZE_FILE,
                temp_image
            ],

            cwd=BASE_DIR,

            capture_output=True,

            text=True,

            timeout=60
        )


        output = result.stdout.strip()


        # -------------------------------
        # Delete temporary image
        # -------------------------------

        if os.path.exists(temp_image):

            os.remove(temp_image)


        # -------------------------------
        # Recognition script error
        # -------------------------------

        if result.returncode != 0:

            return jsonify({

                "status": "error",

                "recognized": False,

                "message":
                    "Face recognition failed.",

                "error":
                    result.stderr,

                "output":
                    output

            }), 500


        # -------------------------------
        # RECOGNIZED
        # -------------------------------

        if output.startswith("RECOGNIZED:"):

            student_name = (
                output
                .replace(
                    "RECOGNIZED:",
                    "",
                    1
                )
                .strip()
            )


            # Mark attendance

            newly_marked = mark_attendance(
                student_name
            )


            if newly_marked:

                message = (
                    f"{student_name} recognized. "
                    "Attendance marked as Present."
                )

            else:

                message = (
                    f"{student_name} recognized. "
                    "Attendance was already marked today."
                )


            return jsonify({

                "status": "success",

                "recognized": True,

                "student_name":
                    student_name,

                "attendance_marked":
                    newly_marked,

                "message":
                    message,

                "output":
                    output

            })


        # -------------------------------
        # UNKNOWN
        # -------------------------------

        return jsonify({

            "status": "success",

            "recognized": False,

            "message":
                "Face not recognized. "
                "Attendance was not marked.",

            "output":
                output

        })


    except subprocess.TimeoutExpired:

        if os.path.exists(temp_image):

            os.remove(temp_image)


        return jsonify({

            "status": "error",

            "recognized": False,

            "message":
                "Face recognition timed out."

        }), 500


    except Exception as e:

        if os.path.exists(temp_image):

            os.remove(temp_image)


        return jsonify({

            "status": "error",

            "recognized": False,

            "message":
                str(e)

        }), 500