from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import sys
import csv
from datetime import datetime


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")

TRAIN_FILE = os.path.join(BASE_DIR, "train.py")
RECOGNIZE_FILE = os.path.join(BASE_DIR, "recognize.py")

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "Attendance.csv"
)

# Create directories if they don't exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "Face Recognition API is running successfully!"
    })


# =========================================================
# REGISTER STUDENT
# =========================================================

@app.route("/register", methods=["POST"])
def register():

    try:

        # -------------------------------------------------
        # GET STUDENT NAME
        # -------------------------------------------------

        student_name = request.form.get(
            "student_name",
            ""
        ).strip()

        if not student_name:

            return jsonify({
                "status": "error",
                "message": "Student name is required."
            }), 400

        # -------------------------------------------------
        # STUDENT DIRECTORY
        # -------------------------------------------------

        student_dir = os.path.join(
            DATASET_DIR,
            student_name
        )

        os.makedirs(
            student_dir,
            exist_ok=True
        )

        # -------------------------------------------------
        # GET IMAGES
        # -------------------------------------------------

        images = request.files.getlist("images")

        if not images:

            return jsonify({
                "status": "error",
                "message": "No images received."
            }), 400

        # -------------------------------------------------
        # SAVE IMAGES
        # -------------------------------------------------

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

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

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

            "message":
                str(e)

        }), 500


# =========================================================
# TRAIN FACE MODEL
# =========================================================

@app.route("/train", methods=["GET", "POST"])
def train():

    try:

        # -------------------------------------------------
        # CHECK TRAIN FILE
        # -------------------------------------------------

        if not os.path.exists(TRAIN_FILE):

            return jsonify({

                "status": "error",

                "message":
                    "train.py not found."

            }), 404

        # -------------------------------------------------
        # RUN TRAIN.PY
        # -------------------------------------------------

        result = subprocess.run(

            [
                sys.executable,
                TRAIN_FILE
            ],

            cwd=BASE_DIR,

            capture_output=True,

            text=True
        )

        # -------------------------------------------------
        # TRAINING ERROR
        # -------------------------------------------------

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

        # -------------------------------------------------
        # TRAINING SUCCESS
        # -------------------------------------------------

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

            "message":
                str(e)

        }), 500


# =========================================================
# MARK ATTENDANCE
# =========================================================

def mark_attendance(student_name):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    current_time = datetime.now().strftime(
        "%H:%M:%S"
    )

    # -----------------------------------------------------
    # CREATE CSV IF IT DOES NOT EXIST
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CHECK DUPLICATE ATTENDANCE
    # -----------------------------------------------------

    with open(
        ATTENDANCE_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            existing_name = (
                row.get(
                    "Student Name",
                    ""
                )
                .strip()
            )

            existing_date = (
                row.get(
                    "Date",
                    ""
                )
                .strip()
            )

            if (
                existing_name.lower()
                == student_name.lower()
                and
                existing_date
                == today
            ):

                return False

    # -----------------------------------------------------
    # SAVE ATTENDANCE
    # -----------------------------------------------------

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


# =========================================================
# VIEW ATTENDANCE
# =========================================================

@app.route("/attendance", methods=["GET"])
def get_attendance():

    try:

        records = []

        # -------------------------------------------------
        # CREATE CSV IF NOT EXISTS
        # -------------------------------------------------

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

            return jsonify({

                "status": "success",

                "records": [],

                "count": 0

            })

        # -------------------------------------------------
        # READ CSV
        # -------------------------------------------------

        with open(
            ATTENDANCE_FILE,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                records.append({

                    "Student Name":
                        row.get(
                            "Student Name",
                            ""
                        ).strip(),

                    "Date":
                        row.get(
                            "Date",
                            ""
                        ).strip(),

                    "Time":
                        row.get(
                            "Time",
                            ""
                        ).strip(),

                    "Status":
                        row.get(
                            "Status",
                            "Present"
                        ).strip()

                })

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "status": "success",

            "records":
                records,

            "count":
                len(records)

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "records": [],

            "message":
                str(e)

        }), 500


# =========================================================
# FACE RECOGNITION
# =========================================================

@app.route("/recognize", methods=["POST"])
def recognize():

    temp_image = os.path.join(
        BASE_DIR,
        "temp_face.jpg"
    )

    try:

        # -------------------------------------------------
        # RECEIVE IMAGE
        # -------------------------------------------------

        image = request.files.get("image")

        if image is None:

            return jsonify({

                "status": "error",

                "recognized": False,

                "message":
                    "No camera image received."

            }), 400

        # -------------------------------------------------
        # CHECK RECOGNIZE.PY
        # -------------------------------------------------

        if not os.path.exists(RECOGNIZE_FILE):

            return jsonify({

                "status": "error",

                "recognized": False,

                "message":
                    "recognize.py not found."

            }), 404

        # -------------------------------------------------
        # CHECK MODEL
        # -------------------------------------------------

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
                    "trainer.yml not found. "
                    "Please train the model."

            }), 400

        if not os.path.exists(labels_file):

            return jsonify({

                "status": "error",

                "recognized": False,

                "message":
                    "labels.pkl not found. "
                    "Please train the model."

            }), 400

        # -------------------------------------------------
        # SAVE TEMP IMAGE
        # -------------------------------------------------

        image.save(temp_image)

        # -------------------------------------------------
        # RUN RECOGNITION
        # -------------------------------------------------

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

        # -------------------------------------------------
        # GET OUTPUT
        # -------------------------------------------------

        output = result.stdout.strip()

        error_output = result.stderr.strip()

        # -------------------------------------------------
        # REMOVE TEMP IMAGE
        # -------------------------------------------------

        if os.path.exists(temp_image):

            os.remove(temp_image)

        # -------------------------------------------------
        # RECOGNITION SCRIPT ERROR
        # -------------------------------------------------

        if result.returncode != 0:

            return jsonify({

                "status": "error",

                "recognized": False,

                "message":
                    "Face recognition failed.",

                "error":
                    error_output,

                "output":
                    output

            }), 500

        # =================================================
        # PARSE RECOGNITION OUTPUT
        # =================================================

        student_name = ""

        confidence = None

        lines = output.splitlines()

        # -------------------------------------------------
        # READ EACH OUTPUT LINE
        # -------------------------------------------------

        for line in lines:

            line = line.strip()

            # ---------------------------------------------
            # RECOGNIZED NAME
            # ---------------------------------------------

            if line.startswith("RECOGNIZED:"):

                student_name = (
                    line
                    .replace(
                        "RECOGNIZED:",
                        "",
                        1
                    )
                    .strip()
                )

            # ---------------------------------------------
            # CONFIDENCE
            # ---------------------------------------------

            elif line.startswith("CONFIDENCE:"):

                confidence_text = (
                    line
                    .replace(
                        "CONFIDENCE:",
                        "",
                        1
                    )
                    .strip()
                )

                try:

                    confidence = float(
                        confidence_text
                    )

                except ValueError:

                    confidence = None

        # =================================================
        # FACE RECOGNIZED
        # =================================================

        if student_name:

            # -------------------------------------------------
            # MARK ATTENDANCE
            # -------------------------------------------------

            newly_marked = mark_attendance(
                student_name
            )

            # -------------------------------------------------
            # MESSAGE
            # -------------------------------------------------

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

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            return jsonify({

                "status":
                    "success",

                "recognized":
                    True,

                "student_name":
                    student_name,

                "confidence":
                    confidence,

                "attendance_marked":
                    newly_marked,

                "message":
                    message,

                "output":
                    output

            })

        # =================================================
        # FACE NOT RECOGNIZED
        # =================================================

        return jsonify({

            "status":
                "success",

            "recognized":
                False,

            "message":
                "Face not recognized. "
                "Attendance was not marked.",

            "output":
                output

        })

    # =====================================================
    # TIMEOUT ERROR
    # =====================================================

    except subprocess.TimeoutExpired:

        if os.path.exists(temp_image):

            os.remove(temp_image)

        return jsonify({

            "status":
                "error",

            "recognized":
                False,

            "message":
                "Face recognition timed out."

        }), 500

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as e:

        if os.path.exists(temp_image):

            os.remove(temp_image)

        return jsonify({

            "status":
                "error",

            "recognized":
                False,

            "message":
                str(e)

        }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5050,

        debug=True

    )