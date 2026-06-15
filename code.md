**DAY 14: LOGIN PAGE DEVELOPMENT**

**db.php**

<?php

$conn = mysqli_connect("localhost","root","","attendance_db");

if(!$conn)

{
    die("Connection Failed");
}

?>

**login.php**

<?php

include("db.php");

$message="";

if(isset($_POST['login']))

{
    $username=$_POST['username'];
    
    $password=$_POST['password'];

    $sql="SELECT * FROM student WHERE username='$username' AND password='$password'";
    
    $result=mysqli_query($conn,$sql);

    if(mysqli_num_rows($result)>0)
    
    {
        $message="Login Successful";
    }
    
    else
    
    {
        $message="Invalid Username or Password";
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

<label>Username</label><br>
                           
<input type="text" name="username" required><br><br>

<label>Password</label><br>

<input type="password" name="password" required><br><br>

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

