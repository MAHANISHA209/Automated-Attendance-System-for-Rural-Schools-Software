**login.php**

<?php

include("db.php");

$message = "";

if(isset($_POST['login']))

{

    $username = $_POST['username'];
    
    $password = $_POST['password'];

    $sql = "SELECT * FROM student WHERE username='admin' AND password='1234'";
    
    $result = mysqli_query($conn, $sql);

    if(mysqli_num_rows($result) > 0)
    
    {
        echo "<script>
        
        alert('Login Successful');
        
        window.location.href='dashboard.php';
        
        </script>";

      
    }
    
    else
    
    {
    
        $message = "Invalid Username or Password";
        
    }
    
}

?>

<!DOCTYPE html>

<html>
    
<head>
    
    <title>Login Page</title>
    
    <link rel="stylesheet" href="style.css">
    
</head>

<body>

<center>
    
    <h2>Login Page</h2>

    <form method="POST">
    
        <label>Username</label><br>
        <input type="text" name="username" required><br><br>

        <label>Password</label><br>
        <input type="password" name="password" required><br><br>

        <input type="submit" name="login" value="Login">
    </form>

    <p><?php echo $message; ?></p>
    
</center>

</body>
    
</html>

**dashboard.php**

<!DOCTYPE html>

<html>
    
<head>
    
    <title>Dashboard</title>
    <link rel="stylesheet" href="style.css">
    
</head>

<body>

<div class="dashboard">

<h1>Automated Attendance System</h1>

<ul>
    <li><a href="registration.php"> Student Registration</a></li>

    <li><a href="capture.php"> Capture Face</a></li>

    <li><a href="train.php"> Train Face</a></li>

    <li><a href="attendance.php"> Mark Attendance</a></li>

    <li><a href="report.php">Attendance Report</a></li>

    <li><a href="login.php"> Logout</a></li>
    
</ul>

</div>

</body>

</html>

**registration.php**

<?php

include("db.php");

$msg="";

if(isset($_POST['register']))
{
    $student_id = $_POST['student_id'];
    
    $student_name = $_POST['student_name'];
    
    $class_name = $_POST['class_name'];

    $sql = "INSERT INTO students(student_id,student_name,class_name)
            VALUES('$student_id','$student_name','$class_name')";

    if(mysqli_query($conn,$sql))
    
    {
    
        $msg = "Student Registered Successfully";
        
    }
    
    else
    
    {
    
        $msg = "Registration Failed";
        
    }
    
}

?>

<!DOCTYPE html>

<html>
    
<head>
    
    <title>Student Registration</title>
    <link rel="stylesheet" href="style.css">
    
</head>

<body>

<div class="login-box">

    <h2>Student Registration</h2>

    <form method="POST">

        <label>Student ID</label>
        <input type="text" name="student_id" required><br><br>

        <label>Student Name</label>
        <input type="text" name="student_name" required><br><br>

        <label>Class</label>
        <input type="text" name="class_name" required><br><br>

        <button type="submit" name="register">Register</button>

    </form>

    <br>

    <a href="capture.php">
    
        <button type="button">Capture Face</button>
    </a>

    <?php
    
    if($msg != "")
    
    {
    
        echo "<p style='color:green;font-weight:bold;'>$msg</p>";
        
    }
    
    ?>

    <br><br>

    <a href="dashboard.php">
        <button type="button">Back to Dashboard</button>
    </a>

</div>

</body>

</html>

**attendance.php**

<!DOCTYPE html>

<html>
    
<head>
    
    <title>Mark Attendance</title>
    <link rel="stylesheet" href="style.css">
    
</head>

<body>

<div class="login-box">

<h2>Mark Attendance</h2>

<p><b>Step 1:</b> Open Command Prompt.</p>

<p><b>Step 2:</b></p>

<pre>
    
cd /d C:\wamp\www\automated\face
    
python recognize.py
    
</pre>

<p><b>Step 3:</b> After face recognition is complete, press <b>ESC</b>.</p>

<p><b>Step 4:</b> Click Finish Attendance.</p>

<a href="finish_attendance.php">
    <button>Finish Attendance</button>
</a>

<br><br>

<a href="report.php">
    <button>View Attendance Report</button>
</a>

</div>

</body>

</html>

**report.php**

<?php
include("db.php");

$sql = "SELECT * FROM face_attendance ORDER BY id ASC";
$result = mysqli_query($conn,$sql);
?>

<!DOCTYPE html>
<html>
<head>
    <title>Attendance Report</title>
    <link rel="stylesheet" href="style.css">
    <style>
.login-box{
    width:1200px;
    height:600px;
    background-color:yellow;
}
</style>
</head>
<body>

<div class="login-box">

<h2>Attendance Report</h2>
<center>
<table  border="2px"  solid width="100px" height="100px">
<tr>
    
    <th>ID</th>
    <th>Student Name</th>
    <th>Date</th>
    <th>Time</th>
    <th>Status</th>
</tr>

<?php
while($row = mysqli_fetch_assoc($result))
{
?>
<tr>
   
    <td><?php echo $row['id']; ?></td>
    <td><?php echo $row['student_name']; ?></td>
    <td><?php echo $row['attendance_date']; ?></td>
    <td><?php echo $row['attendance_time']; ?></td>
    <td><?php echo $row['status']; ?></td>

</tr>
<?php
}
?>

</table>
</center>

</div>

</body>
</html>

**absent.php**
<?php
include("db.php");

$today = date("Y-m-d");

// Get all registered students
$students = mysqli_query($conn, "SELECT student_name FROM students");

while($row = mysqli_fetch_assoc($students))
{
    $name = trim($row['student_name']);

    // Check if attendance already exists for today
    $check = mysqli_query($conn,
    "SELECT * FROM face_attendance
     WHERE student_name='$name'
     AND attendance_date='$today'");

    // If not present, mark as Absent
    if(mysqli_num_rows($check) == 0)
    {
        $sql = "INSERT INTO face_attendance
        (student_name, attendance_date, attendance_time, status)
        VALUES
        ('$name', '$today', '00:00:00', 'Absent')";

        if(mysqli_query($conn, $sql))
        {
            echo "<p style='color:green;'>$name marked Absent</p>";
        }
        else
        {
            echo "<p style='color:red;'>Database Error: ".mysqli_error($conn)."</p>";
        }
    }
}

echo "<br><a href='report.php'><button>View Attendance Report</button></a>";
?>
**db.php**
<?php
$conn = mysqli_connect("localhost","root","","attendance_db");

if(!$conn)
{
    die("Connection Failed");
}
?>
**style.css**
body{
    margin:0;
    padding:0;
    font-family:Arial, Helvetica, sans-serif;
    background:url("./images/images (3).jpg");
    background-size:cover;
    background-position:center;
    background-repeat:no-repeat;
}

.login-box,
.registration-box,
.dashboard{
    width:450px;
    margin:60px auto;
    padding:30px;
    background:rgba(255,255,255,0.95);
    border-radius:15px;
    box-shadow:0 8px 20px rgba(0,0,0,0.3);
}

h1,h2{
    text-align:center;
    color:#00695c;
    margin-bottom:25px;
}

label{
    font-weight:bold;
    display:block;
    margin-top:10px;
}

input[type=text],
input[type=password],
input[type=date]{
    width:100%;
    padding:10px;
    margin-top:5px;
    border:1px solid #ccc;
    border-radius:6px;
    box-sizing:border-box;
}

button{
    width:100%;
    padding:12px;
    margin-top:15px;
    background:#00897b;
    color:white;
    border:none;
    border-radius:6px;
    font-size:16px;
    cursor:pointer;
    transition:0.3s;
}

button:hover{
    background:#00695c;
}

.dashboard ul{
    list-style:none;
    padding:0;
}

.dashboard li{
    margin:18px 0;
}

.dashboard a{
    display:block;
    text-decoration:none;
    background:#1976d2;
    color:white;
    padding:15px;
    border-radius:8px;
    font-size:18px;
    transition:.3s;
}

.dashboard a:hover{
    background:#0d47a1;
}

table{
    width:100%;
    border-collapse:collapse;
    background:white;
}

th{
    background:#1976d2;
    color:white;
}

th,td{
    padding:12px;
    border:1px solid #ddd;
    text-align:center;
}

tr:nth-child(even){
    background:#f5f5f5;
}
**face**
**capture.py**
<!DOCTYPE html>
<html>
<head>
    <title>Capture Face</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="login-box">

<h2>Capture Face</h2>

<p>1. Open Command Prompt</p>

<p>2. Run:</p>

<pre>
cd /d C:\wamp\www\automated\face
python capture.py
</pre>

<p>3. Enter Student Name</p>

<p>4. Wait until 5 images are captured.</p>

<br>

<a href="dashboard.php">
    <button>Back to Dashboard</button>
</a>

</div>

</body>
</html>

**train.py**
import cv2
import os
import numpy as np
import pickle

recognizer = cv2.face.LBPHFaceRecognizer_create()

dataset_path = "dataset"

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

faces = []
labels = []

label_map = {}
current_id = 0

for person in sorted(os.listdir(dataset_path)):

    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    print("Training:", person)

    label_map[current_id] = person

    for img_name in os.listdir(person_path):

        img_path = os.path.join(person_path, img_name)

        img = cv2.imread(img_path)

        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces.append(cv2.resize(gray, (200, 200)))
        labels.append(current_id)

    current_id += 1

faces = np.array(faces)
labels = np.array(labels)

recognizer.train(faces, labels)

# CREATE FOLDER IF NOT EXISTS
os.makedirs("trainer", exist_ok=True)

# SAVE MODEL
recognizer.save("trainer/trainer.yml")

# 🔥 IMPORTANT FIX: SAVE LABELS PROPERLY
with open("trainer/labels.pkl", "wb") as f:
    pickle.dump(label_map, f)

print("Training Completed Successfully")
print("Label Map:", label_map)
**recognize.py**
import cv2
import pickle
import mysql.connector
from datetime import datetime

# ---------------------------
# Load Model
# ---------------------------
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/trainer.yml")

# ---------------------------
# Load Labels
# ---------------------------
with open("trainer/labels.pkl", "rb") as f:
    label_map = pickle.load(f)

label_map = {int(k): v for k, v in label_map.items()}

# ---------------------------
# Face Detector
# ---------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ---------------------------
# Mark Attendance
# ---------------------------
def markAttendance(name):

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="attendance_db"
        )

        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        cursor.execute(
            "SELECT * FROM face_attendance WHERE student_name=%s AND attendance_date=%s",
            (name, today)
        )

        result = cursor.fetchone()

        if result is None:

            cursor.execute(
                "INSERT INTO face_attendance(student_name, attendance_date, attendance_time, status) VALUES (%s,%s,%s,%s)",
                (name, today, current_time, "Present")
            )

            conn.commit()

            print("✔ Attendance Saved :", name)

        else:
            print("Attendance Already Marked :", name)

        cursor.close()
        conn.close()

    except Exception as e:
        print("DATABASE ERROR :", e)


# ---------------------------
# Open Camera
# ---------------------------
cam = cv2.VideoCapture(0)

marked = set()

while True:

    ret, frame = cam.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        roi = gray[y:y+h, x:x+w]
        roi = cv2.resize(roi, (200, 200))

        id_, confidence = recognizer.predict(roi)

        if confidence < 75:

            name = label_map.get(int(id_), "Unknown")

            if name not in marked:
                markAttendance(name)
                marked.add(name)

        else:
            name = "Unknown"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(
            frame,
            name,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

        
