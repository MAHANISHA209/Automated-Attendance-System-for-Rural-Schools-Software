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

    width:250px;
    
    margin:100px ;
    
    padding:30px;
    
    background-color:white;
    
    border-radius:5px;
    
    box-shadow:0px 0px 10px gray;
    
}

h2{

    text-align:center;
    
    color:#c12c2c;
}

label{
    font-weight:bold;
}

input{

    width:200px;
    
    height:30px;
    
    padding:5px;
    
    margin-top:5px;
    
    margin-bottom:15px;
    
    border:2px;
    
    border-radius:5px;
    
    box-sizing:border-box;
}

button{

    width:100px;
    
    height:35px;
    
    padding:10px;
    
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

