import cv2
import os
import pickle
import sys

# ==========================================
# PATHS
# ==========================================

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


# ==========================================
# CHECK INPUT IMAGE
# ==========================================

if len(sys.argv) < 2:

    print("ERROR: Input image not provided.")
    sys.exit(1)

IMAGE_PATH = sys.argv[1]


if not os.path.exists(IMAGE_PATH):

    print("ERROR: Input image not found.")
    sys.exit(1)


# ==========================================
# CHECK MODEL
# ==========================================

if not os.path.exists(TRAINER_PATH):

    print("ERROR: trainer.yml not found.")
    sys.exit(1)


if not os.path.exists(LABELS_PATH):

    print("ERROR: labels.pkl not found.")
    sys.exit(1)


# ==========================================
# LOAD IMAGE
# ==========================================

image = cv2.imread(IMAGE_PATH)

if image is None:

    print("ERROR: Could not read image.")
    sys.exit(1)


# ==========================================
# LOAD FACE DETECTOR
# ==========================================

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


# ==========================================
# LOAD LBPH MODEL
# ==========================================

try:

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read(TRAINER_PATH)

except Exception as e:

    print(
        "ERROR: Could not load LBPH model: "
        + str(e)
    )

    sys.exit(1)


# ==========================================
# LOAD LABELS
# ==========================================

try:

    with open(
        LABELS_PATH,
        "rb"
    ) as file:

        label_map = pickle.load(file)

except Exception as e:

    print(
        "ERROR: Could not load labels.pkl: "
        + str(e)
    )

    sys.exit(1)


# ==========================================
# CONVERT IMAGE TO GRAYSCALE
# ==========================================

gray = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)


# ==========================================
# DETECT FACE
# ==========================================

faces = face_detector.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(100, 100)
)


if len(faces) == 0:

    print("UNKNOWN: No face detected.")
    sys.exit(0)


# ==========================================
# RECOGNIZE FACE
# ==========================================

best_name = None
best_confidence = 999


for (x, y, w, h) in faces:

    face = gray[
        y:y + h,
        x:x + w
    ]

    face = cv2.resize(
        face,
        (200, 200)
    )

    try:

        student_id, confidence = (
            recognizer.predict(face)
        )

    except Exception as e:

        print(
            "ERROR: Face prediction failed: "
            + str(e)
        )

        sys.exit(1)


    if confidence < best_confidence:

        best_confidence = confidence

        best_name = label_map.get(
            student_id,
            "Unknown"
        )


# ==========================================
# CHECK RECOGNITION
# ==========================================

# Lower LBPH confidence = better match
THRESHOLD = 70


if (
    best_name is not None
    and best_name != "Unknown"
    and best_confidence < THRESHOLD
):

    print(
        "RECOGNIZED:"
        + str(best_name)
    )

    print(
        "CONFIDENCE:"
        + str(round(best_confidence, 2))
    )

    sys.exit(0)


print(
    "UNKNOWN: Face not recognized."
)

sys.exit(0)