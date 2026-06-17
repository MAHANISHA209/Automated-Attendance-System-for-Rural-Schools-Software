**DAY 14: LOGIN PAGE DEVELOPMENT**

**db.php**

<?php
$conn = mysqli_connect("localhost", "root", "", "attendance_db");

if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
?>
**login.php**

<?php
include("db.php");
$message = "";

if (isset($_POST['login'])) {

    $username = $_POST['username'];
    $password = $_POST['password'];

    $sql = "SELECT * FROM users WHERE username='$username' AND password='$password'";
    $result = mysqli_query($conn, $sql);

    if (mysqli_num_rows($result) > 0) {
        $message = "Login Successful";
    } else {
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

<div class="login-box">
    <h2>Login</h2>

    <form method="POST">

        <label>Username</label>
        <input type="text" name="username" required>

        <label>Password</label>
        <input type="password" name="password" required>

        <button type="submit" name="login">Login</button>

    </form>

    <p><?php echo $message; ?></p>

</div>

</body>
</html>

**style.css**

body{
    margin:0;
    
    padding:0;
    
    font-family:Arial, sans-serif;
    
    background-color:#87CEEB;
    
}


.login-box{

    width:350px;
    
    margin:100px auto;
    
    padding:30px;
    
    background-color:white;
    
    border-radius:10px;
    
    box-shadow:0px 0px 10px gray;
    
}

h2{
    text-align:center;
    
    color:#c12c2c;
    
}

label{

    font-weight:bold;
    
}

input[type="text"],
input[type="date"]{

    width:200px;
    
    height:30px;
    
    padding:5px;
    
    margin-top:5px;
    
    margin-bottom:15px;
    
    border:1px solid #ccc;
    
    border-radius:5px;
    
    box-sizing:border-box;
    
}
input[type="radio"]{

    width:auto ;
    
    height:auto ;
    
    padding:0 ;
    
    margin:0 5px 0 0 ;
    
    vertical-align:middle;
    
}



button{

    width:100px;
    
    height:35px;
    
    background-color:green;
    
    color:white;
    
    border:none;
    
    border-radius:5px;
    
    cursor:pointer;
    
}

button:hover{

    background-color:darkgreen;
    
}


.registration-box{

    width:300px;
    
    margin:100px auto;
    
    padding:30px;
    
    background-color:white;
    
    border-radius:10px;
    
    box-shadow:0px 0px 10px gray;
    
    text-align: center;
    
}

.dashboard{

    width:400px;
    
    margin:100px auto;
    
    padding:20px;
    
    background:white;
    
    border-radius:5px;
    
    box-shadow:0px 0px 10px gray;
    
    text-align:center;
    
}

.dashboard ul{

    list-style:none;
    
    padding:0;
    
}

.dashboard li{

    margin:15px 0;
    
}

.dashboard a{

    text-decoration:none;
    
    color:white;
    
    background-color:rgb(215, 139, 101);
    
    padding:10px 20px;
    
    border-radius:5px;
    
    display:inline-block;
    
}
table{

    width:100%;
    
    border-collapse:collapse;
    
    
}

th,td{

    padding:10px;
    
    text-align:center;
    
    border:1px solid black;
    
}

h2{

    margin-bottom:30px;
    
}

**DAY 15:REGIRATION PAGE DEVELOPMENT**

**regiration.php**

?php

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
        <input type="text" name="student_id" required>

        <label>Student Name</label>
        <input type="text" name="student_name" required>

        <label>Class</label>
        <input type="text" name="class_name" required>

        <button type="submit" name="register">Register</button>

    </form>

    <p><?php echo $msg; ?></p>

</div>

</body>

</html>

**Day 16 : DASHBOARD DEVELOPMENT**

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
    
    <li><a href="registration.php">Student Registration</a></li>
    
    <li><a href="attendance.php">Mark Attendance</a></li>
    
    <li><a href="report.php">Attendance Report</a></li>
    
    <li><a href="login.php">Logout</a></li>
    
</ul>

</div>

</body>

</html>

**DAY 17: CRUD OPERATION**

**attendance.php** 

<?php

include("db.php");

$msg="";

if(isset($_POST['submit']))

{
    $student_id = $_POST['student_id'];
    
    $attendance_date = $_POST['attendance_date'];
    
    $status = $_POST['status'];

    $sql = "INSERT INTO attendance(student_name, att_date, status)
    
            VALUES('$student_id','$attendance_date','$status')";

    if(mysqli_query($conn,$sql))
    
    {
        $msg = "Attendance Saved Successfully";
        
    }
    else{
    
        echo mysqli_error($conn);
    }

}

?>

<!DOCTYPE html>

<html>
    
<head>
    
    <title>Attendance Page</title>
    
    <link rel="stylesheet" href="style.css">
    
</head>

<body>

<div class="login-box">

<h2>Mark Attendance</h2>

<form method="POST">

<label>Student ID</label><br>

<input type="text" name="student_id" required><br><br>

<label>Date</label><br>

<input type="date" name="attendance_date" required><br><br>

<label>Status</label><br>

<input type="radio" name="status" value="Present" required> Present


<input type="radio" name="status" value="Absent"> Absent


<br><br>

<button type="submit" name="submit">Submit</button>

</form>

<p><?php echo $msg; ?></p>

</div>

</body>
</html>

**report.php**

?php

include("db.php");

$sql = "SELECT * FROM attendance";

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
    
    <th>Status</th>
    
    <th>Edit</th>
    
    <th>Delete</th>
    
</tr>

<?php

while($row = mysqli_fetch_assoc($result))

{

?>

<tr>
    <td><?php echo $row['id']; ?></td>
    
    <td><?php echo $row['student_name']; ?></td>
    
    <td><?php echo $row['att_date']; ?></td>
    
    <td><?php echo $row['status']; ?></td>
    
    <td>
    
        <a href="edit.php?id=<?php echo $row['id']; ?>">Edit</a>
        
    </td>
    
    <td>
        <a href="delete.php?id=<?php echo $row['id']; ?>">Delete</a>
        
    </td>
    
</tr>

<?php

}

?>

</table>

</center>

</div>

</body>

</html>

**edit.php**

<?php

include("db.php");

$id = $_GET['id'];

$result = mysqli_query($conn,"SELECT * FROM attendance WHERE id=$id");

$row = mysqli_fetch_assoc($result);

if(isset($_POST['update']))

{
    $status = $_POST['status'];

    mysqli_query($conn,"UPDATE attendance SET status='$status' WHERE id=$id");

    header("Location: report.php");
    
}

?>

<form method="POST">
    
    <h2>Edit Attendance</h2>

    <input type="radio" name="status" value="Present"> Present
    
    <input type="radio" name="status" value="Absent"> Absent

    <br><br>

    <button type="submit" name="update">Update</button>
    
</form>

**delete.php**

<?php

include("db.php");

$id = $_GET['id'];

mysqli_query($conn,"DELETE FROM attendance WHERE id=$id");

header("Location: report.php");

?>
