import cv2
import os


def capture_faces(student_name, total_images=20):

    base_dir = os.path.dirname(os.path.abspath(__file__))

    dataset_dir = os.path.join(
        base_dir,
        "dataset"
    )

    student_dir = os.path.join(
        dataset_dir,
        student_name
    )

    os.makedirs(
        student_dir,
        exist_ok=True
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return {
            "status": "error",
            "message": "Camera could not be opened."
        }

    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )

    count = 0

    while count < total_images:

        ret, frame = camera.read()

        if not ret:
            break

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_detector.detectMultiScale(
            gray,
            1.3,
            5
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

            count += 1

            image_path = os.path.join(
                student_dir,
                f"{count}.jpg"
            )

            cv2.imwrite(
                image_path,
                face
            )

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"{count}/{total_images}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            break

        cv2.imshow(
            "Face Registration",
            frame
        )

        if cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()

    return {
        "status": "success",
        "student_name": student_name,
        "images_captured": count,
        "message": "Face capture completed."
    }