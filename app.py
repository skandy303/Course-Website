# required imports
# the sqlite3 library allows us to communicate with the sqlite database
import sqlite3
# we are adding the import 'g' which will be used for the database
from flask import Flask, render_template, request, g,session, redirect, url_for, escape

# the database file we are going to communicate with
DATABASE = 'assignment3.db'

# connects to the database
def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
# (don't worry if you don't understand this code)
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))
def updateDatabase(sqlQuery: str, values: tuple):
    db = get_db()
    cur = db.cursor()
    cur.execute(sqlQuery, values)
    db.commit()
    cur.close()
# given a query, executes and returns the result
# (don't worry if you don't understand this code)
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# tells Flask that "this" is the current running app
app = Flask(__name__)
app.secret_key=b'dan'

# this function gets called when the Flask app shuts down
# tears down the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()

@app.route('/')
def index():
	if 'username' in session:
		if session['type'] =='student':
			return redirect(url_for('studenthome'))
		else:
			return redirect(url_for('instructorhome'))
	return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='POST':
		sql = """
			SELECT *
			FROM users
			"""
		results = query_db(sql, args=(), one=False)
		for result in results:
			if result[1]==request.form['username']:
				if result[2]==request.form['password']:
					session['name']=result[3]
					session['username']=request.form['username']
					session['type']=result[0]
					return redirect(url_for('index'))
		return render_template('loginError.html')
	elif 'username' in session:
		return redirect(url_for('index'))
	else:
		return render_template('login.html')

@app.route('/signup',methods=['GET','POST'])	
def signup():

	if request.method=='POST':
		sql = """
			SELECT *
			FROM users
			"""
		results = query_db(sql, args=(), one=False)
		for result in results:
			if result[1]==request.form['username']:
				return "Username Exists Already"
		
		name=request.form.get('name')
		user=request.form.get('username')
		passw=request.form.get('password')

		if request.form.get('instructor')=='yes':
			updateDatabase('INSERT INTO users VALUES (?,?,?,?)', ('instructor', user, passw, name))


		else:
			updateDatabase('INSERT INTO users VALUES (?,?,?,?)', ('student', user, passw, name))
			updateDatabase('INSERT INTO Students(username, name) VALUES (?,?)', (user, name))

		return redirect(url_for('login'))

	elif 'username' in session:
		return redirect(url_for('index'))
	else:
		return render_template('signup.html')	


@app.route('/studenthome' ,methods=['GET','POST'])	
def studenthome():
	if 'username' not in session or session['type'] =='instructor':
		return render_template('badStudent.html')	
	return render_template('student.html', name=session['name'])

@app.route('/instructorhome' ,methods=['GET','POST'])	
def instructorhome():
	if 'username' not in session or session['type'] =='student':
		return render_template('badInstructor.html')	
	return render_template('instructor.html', name=session['name'])	

@app.route('/grades' ,methods=['GET','POST'])	
def grades():
	if 'username' not in session or session['type'] =='instructor':
		return render_template('badStudent.html')


	if request.method=='POST':
		sql = """
			SELECT *
			FROM Regrade
			"""
		results = query_db(sql, args=(), one=False)

		for result in results:
			if result[0]==session['name'] and result[1]==request.form['regrade_assignment']:
				return render_template('submissionExists.html')
			
		user=session['name']
		assignment=request.form.get('regrade_assignment')
		message=request.form.get('message')

		updateDatabase('INSERT INTO Regrade VALUES (?,?,?)', (user, assignment, message))

		return render_template('submissionSuccess.html')



	grades=query_db("SELECT Assignment1, Assignment2, Assignment3 FROM Students WHERE username=?",(session['username'],))
	return render_template('grades.html', grade=grades)	


@app.route('/feedback' ,methods=['GET','POST'])	
def feedback():
	if 'username' not in session or session['type'] =='instructor':
		return render_template('badStudent.html')


	if request.method=='POST':
	
		instructor=request.form.get('feedback_instructor')
		feedback=request.form.get('feedback')

		updateDatabase('INSERT INTO Feedback VALUES (?,?)', (instructor, feedback))

		return render_template('submissionSuccess.html')

	db = get_db()
	db.row_factory = make_dicts
	iNames = []
	for name in query_db("SELECT name FROM users where id = 'instructor' "):
		iNames.append(name)
	return render_template('feedback.html', namai = iNames)	


@app.route('/gradesView', methods = ['GET', 'POST'])
def gview():
	if 'username' not in session or session['type'] =='student':
		return render_template('badStudent.html')
	db = get_db()
	db.row_factory = make_dicts
	gv = []
	for row in query_db("SELECT name,Assignment1,Assignment2, Assignment3 FROM Students"):
		gv.append(row)
	return render_template('viewGrades.html', gradesview=gv)


@app.route('/feedbackView')
def feedbackView():
	if 'username' not in session or session['type'] =='student':
		return render_template('badInstructor.html')
	
	db = get_db()
	db.row_factory = make_dicts
	gv = []
	for row in query_db("SELECT * FROM Feedback"):
		gv.append(row)

	return render_template('reviewFeedback.html', gradesview=gv)	

@app.route('/regradeView')
def regradeView():
	if 'username' not in session or session['type'] =='student':
		return render_template('badInstructor.html')

	db = get_db()
	db.row_factory = make_dicts
	gv = []
	for row in query_db("SELECT * FROM Regrade"):
		gv.append(row)

	return render_template('reviewRegrade.html', gradesview=gv)	

@app.route('/gradesChange', methods = ['GET', 'POST'])
def gradesChange():
	if 'username' not in session or session['type'] =='student':
		return render_template('badInstructor.html')
	#
	#
	#query all students (similar to querying profin drop table) and pass in template
	#

	if request.method=='POST':
		assignment=request.form.get('regrade_assignment')
		name=request.form.get('studentName')
		grade=request.form.get('new_grade')
		
		if assignment=="Assignment1":
			updateDatabase('UPDATE Students SET Assignment1 = ? WHERE name = ?', (grade, name))
			updateDatabase('DELETE FROM Regrade  WHERE assignment = ? AND name=?',("A1",name))

		if assignment=="Assignment2":
			updateDatabase('UPDATE Students SET Assignment2 = ? WHERE name = ?', (grade, name))	
			updateDatabase('DELETE FROM Regrade  WHERE assignment = ? AND name=?',("A2",name))

		if assignment=="Assignment3":
			updateDatabase('UPDATE Students SET Assignment3 = ? WHERE name = ?', (grade, name))
			updateDatabase('DELETE FROM Regrade WHERE assignment = ? AND name=?',("A3",name))


		return render_template('submissionSuccess.html')
		

		
	db = get_db()
	db.row_factory = make_dicts
	gv = []
	for row in query_db("SELECT name FROM Students "):
		gv.append(row)

	return render_template("changeGrades.html", students=gv)

@app.route('/home')
def home():
	if 'username' not in session:
		return render_template('badlogin.html')	
	return render_template('index.html')


@app.route('/news')
def news():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('News.html')

@app.route('/calendar')
def calendar():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('Calendar.html')

@app.route('/assignments')
def assignments():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('Assignments.html')

@app.route('/labs')
def labs():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('Labs.html')

@app.route('/lectures')
def lectures():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('Lectures.html')

@app.route('/courseteam')
def courseteam():
	if 'username' not in session:
		return render_template('badlogin.html')	

	return render_template('CourseTeam.html')

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('login'))
if __name__=="__main__":
	app.run(debug=True)