import cv2
import os
import pickle
import csv
from datetime import datetime

# -----------------------------------------
# Paths
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "model")

TRAINER_PATH = os.path.join(
    MODEL_DIR,
    "trainer.yml"
)

LABELS_PATH = os.path.join(
    MODEL_DIR,
    "labels.pkl"
)

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "Attendance.csv"
)

# -----------------------------------------
# Check model files
# -----------------------------------------

if not os.path.exists(TRAINER_PATH):
    print("ERROR: trainer.yml not found.")
    exit()

if not os.path.exists(LABELS_PATH):
    print("ERROR: labels.pkl not found.")
    exit()

# -----------------------------------------
# Create Attendance.csv header
# -----------------------------------------

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

# -----------------------------------------
# Load face detector
# -----------------------------------------

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

# -----------------------------------------
# Load LBPH model
# -----------------------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.read(TRAINER_PATH)

# -----------------------------------------
# Load student labels
# -----------------------------------------

with open(
    LABELS_PATH,
    "rb"
) as file:

    label_map = pickle.load(file)

print("Students loaded:")

for student_id, student_name in label_map.items():

    print(
        student_id,
        "->",
        student_name
    )

# -----------------------------------------
# Attendance function
# -----------------------------------------

def mark_attendance(student_name):

    today = datetime.now().strftime("%Y-%m-%d")

    current_time = datetime.now().strftime("%H:%M:%S")

    # Check existing attendance

    if os.path.exists(ATTENDANCE_FILE):

        with open(
            ATTENDANCE_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if (
                    row["Student Name"] == student_name
                    and row["Date"] == today
                ):

                    print(
                        f"{student_name} already marked today."
                    )

                    return

    # Save attendance

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

    print(
        f"Attendance marked: {student_name}"
    )

# -----------------------------------------
# Start camera
# -----------------------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Camera could not be opened.")

    exit()

print()
print("================================")
print("FACE RECOGNITION + ATTENDANCE")
print("================================")
print("Press Q to stop.")

# -----------------------------------------
# Recognition loop
# -----------------------------------------

while True:

    success, frame = camera.read()

    if not success:

        print("ERROR: Could not read camera.")

        break

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

    for (x, y, w, h) in faces:

        face = gray[
            y:y+h,
            x:x+w
        ]

        face = cv2.resize(
            face,
            (200, 200)
        )

        student_id, confidence = recognizer.predict(face)

        # Lower LBPH confidence = better match

        if confidence < 70:

            student_name = label_map.get(
                student_id,
                "Unknown"
            )

            # Mark attendance

            mark_attendance(student_name)

            display_text = (
                student_name
                + " - Present"
            )

        else:

            display_text = "Unknown"

        # Draw face rectangle

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

        # Display name

        cv2.putText(
            frame,
            display_text,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "Face Recognition - Attendance",
        frame
    )

    # Press Q to stop

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break

# -----------------------------------------
# Close camera
# -----------------------------------------

camera.release()

cv2.destroyAllWindows()

print()
print("Face recognition stopped.")