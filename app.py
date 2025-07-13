from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = 'your secret key'

# Enter your database sconnection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'GZTgzt1126'
app.config['MYSQL_DB'] = 'expenses_project'

# Intialize MySQL
mysql = MySQL(app)

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        return render_template('index.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        if user:
            session['logged_in'] = True
            session['username'] = username
            session['id'] = user[0]
            return redirect(url_for('home'))
        else:
            msg = "Invalid username or password"
    return render_template('login.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        
        # Check if username already exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            msg = "Username already exists! Please choose a different username."
            return render_template('register.html', msg=msg)
        
        # If username doesn't exist, insert new user
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        msg = "You have successfully registered, Please login to continue"
        return render_template('login.html', msg=msg)
    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)