● Title:

AcademicWorld Dashboard

● Purpose:

The primary application scenarios are: (i) institution data management to maintain records of faculty and university affiliations and (ii) research collaboration discovery to find potential collaborators.

Target users are: university administrators managing faculty records and affiliations, research offices and department deans analyzing inter-university collaborations, and faculty looking for potential collaborators.

Objectives are to: (i) manage universities and faculty affiliations with universities and (ii) find co-authors by faculty at different universities.

● Demo:

Link to video demo.
https://mediaspace.illinois.edu/media/t/1_oa2t91oo

● Installation:

Copy the following files to the same directory:
api.py
app.py
callbacks.py
client.py
config.py
db.py
main.py
ui.py
requirements.txt

In the same directory, create a file:
config.json

such that config.json contains the following json data:
{
	"mysql":	{
		"host": "<YOUR_HOST_ADDRESS, SUCH AS 127.0.0.1>",
		"user": "<YOUR_MYSQL_USERNAME>",
		"password": "<YOUR_MYSQL_PASSWORD>",
		"database": "academicworld",
		"port": 3306
  },
  "mongo": {
		"host": "<YOUR_HOST_ADDRESS, SUCH AS 127.0.0.1>",
		"database": "academicworld",
		"port": 27017
  },
  "neo4j": {
		"host": "<YOUR_HOST_ADDRESS, SUCH AS 127.0.0.1>",
		"user": "<YOUR_NEO4J_USERNAME>",
		"password": "<YOUR_NEO4J_PASSWORD>",
		"database": "academicworld",
		"db_path": "<ABSOLUTE_PATH_TO_YOUR_NEO4J_ACADEMICWORLD_DATABASE>" 
  }
}

For Python, install the dependencies:
pip install -r requirements.txt

As an alternative to requirements.txt, install the dependencies: 
pip install dash flask sqlalchemy pymongo neo4j pymysql requests

For Windows users, modify the Environmental Variables Path by adding the following (or the user's equivalent installed versions or actual  paths):
C:\Program Files\MySQL\MySQL Server 9.6\bin
C:\Program Files\MongoDB\mongodb-database-tools-windows-x86_64-100.16.0\bin\
C:\Program Files\Neo4j Desktop 2\resources\offline\dbmss\neo4j-enterprise-2026.01.4\bin\

Execute Neo4j Desktop and start instance with academicworld database.

Execute main.py

● Usage:

There are 3 main usages.

1. University Management: Merge or Add a University

To add a university, select "Add University" radio button, enter the new university name into the textbox, and click the "Confirm Add" button. The system adds the university record if it does not already exist.

To merge universities, select "Merge University radio button, choose a first university to remove and a second university to merge into, then click the "Confirm Merge" button. Faculty affiliated with the first university are reassigned to the second university and then the first university is removed.

2. Faculty University Affiliation Management: Change University Affiliation of a Faculty Member

Select a faculty member from the faculty dropdown. The dashboard displays the faculty member’s current university affiliation. Then select a new university affiliation and click the "Confirm Change" button. The faculty member’s university affiliation is updated to the new university.

3. Find Publications Co-Authored by Faculty at Selected Universities

First, choose two universities, left and right universities. The dashboard loads faculty from each university who are co-authors with faculty from the other university.  Then select one faculty member from each side. The dashboard loads publications co-authored by the selected faculty member, and with at least one faculty member affiliated the other university. Finally, select a publication to view detailed publication information from Neo4j (on the left) and MongoDB (on the right).

● Design: What is the design of the application?

The application is divided into the following files with specific responsibilities.

1. main.py

Application entry point
Imports API routes (api.py) and callbacks (callbacks.py)
Assigns the UI:
app.layout = layout

2. app.py
Creates the Dash app
Exposes the Flask server:
Defines shared config like API_BASE_URL

3. ui.py
Defines the frontend, with dashboard layout and UI components that the user sees.

4. callbacks.py
Frontend logic
Contains all Dash callbacks
Handles user interactions (button clicks, dropdown changes) and decision logic (GET, POST, PATCH requests)
Calls API via client.py

5. client.py
API client bridging frontend to backend.
Sends HTTP requests using Requests.
Wraps API calls.

6. api.py
Backend API layer
Defines Flask REST endpoints
@server.get(...)
@server.post(...)
@server.patch(...)
Request parsing, validation, error handling, calls database functions in db.py

7. db.py
Contains database logic
Executes MySQL queries, MongoDB queries, Neo4j queries

8. config.py
Loads configuration from file
Initializes database connections with MySQL, MongoDB, Neo4j

● Implementation: How did you implement it? What frameworks and libraries or any tools have you used to realize the dashboard and functionalities?

The application was implemented as a full-stack Python web application.

The frontend was built with Dash.  The backend REST API was implemented with Flask.
The frontend communicates with the backend through HTTP requests via the Requests library.
Database access utilized SQLAlchemy with PyMySQL to access MySQL, PyMongo to access MongoDB, and Neo4j to access Neo4j. 

The main libraries used were:

dash
flask
sqlalchemy
pymongo
neo4j
pymysql
requests

● Database Techniques: What database techniques have you implemented? How?

I implemented the four database techniques: 5. Stored procedure, 6. Prepared statements, 7. Transaction, and 10. REST API.

(5) Stored procedure was implemented in the file db.py as two stored procedures, in the Python functions:
add_university_procedure(), which creates the MySQL procedure add_university that inserts a new university.
merge_university_procedure(), which creates the MySQL procedure merge_universities that merges two universities by changing faculty affiliations from a first university to a second university and then deletes the first university.
Both the add_university and merge_universities MySQL procedures are created by respective CREATE PROCEDURE statements in SQL.

(6) Prepared statements was implemented in the file db.py in the Python function add_university_procedure(), and within the MySQL stored procedure add_university.  The PREPARE statement in MySQL defines a parameterized SQL INSERT query.  The input parameter added_university_name of the MySQL procedure add_university is assigend to a variable and passed into the the prepared statement prep_stmt using the EXECUTE...USING MySQL clause.

(7) Transaction was implemented in the file db.py in the Python function merge_university_procedure(), and within the MySQL stored procedure merge_universities.  The purpose of a transaction is to complete multiple MySQL operations atomically, such that all operations succeed or none are applied.  In this case, the transaction guarantees that, faculty affiliations are successfully updated from a first university to a second university, before the first university is deleted.  If any step fails, the changes are rolled back.  The transaction begins with the MySQL statement START TRANSACTION, ends with the MySQL statement COMMIT, and upon a failure performs the MySQL statement ROLLBACK.

(10) REST API was implemented in the Python files api.py, callbacks.py, and client.py.
In callbacks.py, Dash callbacks handle user interactions like button clicks and dropdown selections to issue http requests GET, POST, and PATCH.  In api.py, REST endpoints receive the HTTP requests.  A helper function in client.py is used to format the HTTP requests in JSON and parses JSON responses.  In api.py, Flask defines REST endpoints using route decorators (@server.get, @server.post, @server.patch). The REST endpoints receive the HTTP requests and invoke database functions in db.py.  Then the REST endpoints return JSON responses with HTTP status codes (200 for success, 400 for invalid input, 500 for server errors).
Flask provides the added advantage of implementing the REST API for all three databases, including MongoDB, rather than just MySQL and Neo4j.

● Extra-Credit Capabilities: What extra-credit capabilities have you developed if any?

A first extra-credit capability is the implementation of four database techniques, exceeding the requirement of three database techniques.

A second extra-credit capability is multi-database querying in three steps.  
1) MySQL is used to retrieve publication IDs
2) both MongoDB and Neo4j are queried using those publication IDs to retrieve detailed publication information.
The MongoDB endpoint @server.get("/api/mongo/publications/<int:publication_id>") and the neo4j endpoint @server.get("/api/neo4j/publications/<int:publication_id>") are dependent on publication IDs that were retrieved with the MySQL endpoint  @server.get("/api/faculty/<int:faculty_id>/publications").
3) MySQL is used to retrieve all authors for those publication IDs.

● Contributions: How each member has contributed, in terms of 1) tasks done and 2) time spent?

This was a solo project.

