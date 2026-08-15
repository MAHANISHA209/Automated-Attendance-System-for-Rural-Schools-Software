import cv2
import os
import pickle
import numpy as np

# -----------------------------------------
# Paths
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")

os.makedirs(MODEL_DIR, exist_ok=True)

TRAINER_PATH = os.path.join(
    MODEL_DIR,
    "trainer.yml"
)

LABELS_PATH = os.path.join(
    MODEL_DIR,
    "labels.pkl"
)

# -----------------------------------------
# Check dataset
# -----------------------------------------

if not os.path.exists(DATASET_DIR):

    print("ERROR: Dataset folder not found.")
    exit()

# -----------------------------------------
# Face detector
# -----------------------------------------

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

# -----------------------------------------
# LBPH recognizer
# -----------------------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
labels = []

label_map = {}

current_id = 0

# -----------------------------------------
# Read student folders
# -----------------------------------------

student_folders = sorted(
    os.listdir(DATASET_DIR)
)

for student_name in student_folders:

    student_path = os.path.join(
        DATASET_DIR,
        student_name
    )

    # Ignore files
    if not os.path.isdir(student_path):
        continue

    label_map[current_id] = student_name

    print()
    print("Training:", student_name)

    image_files = os.listdir(student_path)

    for image_file in image_files:

        image_path = os.path.join(
            student_path,
            image_file
        )

        image = cv2.imread(
            image_path,
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            continue

        detected_faces = face_detector.detectMultiScale(
            image,
            scaleFactor=1.1,
            minNeighbors=5
        )

        # If the saved image is already a face crop,
        # use the complete image when no face is detected.
        if len(detected_faces) == 0:

            face = cv2.resize(
                image,
                (200, 200)
            )

            faces.append(face)
            labels.append(current_id)

        else:

            for (x, y, w, h) in detected_faces:

                face = image[
                    y:y+h,
                    x:x+w
                ]

                face = cv2.resize(
                    face,
                    (200, 200)
                )

                faces.append(face)
                labels.append(current_id)

    current_id += 1

# -----------------------------------------
# Check training data
# -----------------------------------------

if len(faces) == 0:

    print()
    print("ERROR: No face images found.")
    print()
    print("Add student images inside:")
    print(DATASET_DIR)

    exit()

# -----------------------------------------
# Convert labels
# -----------------------------------------

labels = np.array(
    labels,
    dtype=np.int32
)

# -----------------------------------------
# Train LBPH model
# -----------------------------------------

print()
print("================================")
print("TRAINING MODEL")
print("================================")

recognizer.train(
    faces,
    labels
)

# -----------------------------------------
# Save model
# -----------------------------------------

recognizer.write(
    TRAINER_PATH
)

with open(
    LABELS_PATH,
    "wb"
) as file:

    pickle.dump(
        label_map,
        file
    )

# -----------------------------------------
# Finished
# -----------------------------------------

print()
print("================================")
print("TRAINING COMPLETED")
print("================================")

print("Images used:", len(faces))

print("Students:")

for student_id, name in label_map.items():
    print(
        student_id,
        "->",
        name
    )

print()
print("Model saved:")
print(TRAINER_PATH)

print()
print("Labels saved:")
print(LABELS_PATH)