# Quiz Master - V1
It is a multi-user app (one requires an administrator and other users) that acts as an exam preparation site for multiple courses.

## Framewords used:
  Flask for application back-end
  Jinja2 templating, HTML, CSS and Bootstraps for application front-end
  SQLite for database

## How to Run?
1. Download the ZIP file and extract it.
2. Open a terminal and navigate to the extracted folder.
3. Run the following command: python app.py
4. Open your browser and go to http://127.0.0.1:5000/.

### Admin Login
- Username: quizmaster
- Password: admin123
- Admins can create subjects, chapters, quizzes, and add questions.
  
### User Signup & Login
- Users can register, take quizzes, view scores, and compare their performance with the class average.

### Query for Stored XSS attack demo
- Paste the text below in the feedback section on the index page.
- For instance you may use something like -
  <script>
    document.body.style.backgroundColor = "black";
    document.body.style.color = "red";
    alert('You are now under my control..This website has been hacked!!!');
</script>

### Query for Reflected XSS attack demo
- Go to user's dashboard, implement any html tag in the search box.
- For instance you may use something like -
  <script>
  alert('Reflected XSS')
  </script>

### Query for SQL injection
- Go to Home Page and enter the following credentials
  Field | Value
  Username | ' OR '1'='1' --
  Password | anything