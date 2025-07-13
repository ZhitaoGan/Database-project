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

# helper functions
def grab_user_transactions(user_id):
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT t.transaction_id, t.date, t.amount, t.description, t.user_id, c.category_name, t.category_id
        FROM Transactions t 
        INNER JOIN Category c ON t.category_id = c.category_id 
        WHERE t.user_id = %s 
        ORDER BY t.date DESC
    """, (user_id,))
    
    transactions = cur.fetchall()
    cur.close()
    return transactions

def get_user_statistics(user_id):
    cur = mysql.connection.cursor()
    
    # Get basic statistics (total transactions, total expenses, largest expense)
    cur.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(t.amount) as total_expenses,
            MAX(t.amount) as largest_expense
        FROM Transactions t 
        WHERE t.user_id = %s
    """, (user_id,))
    basic_stats = cur.fetchone()
    
    # Get most spent category
    cur.execute("""
        SELECT c.category_name, SUM(t.amount) as total_spent
        FROM Transactions t 
        INNER JOIN Category c ON t.category_id = c.category_id 
        WHERE t.user_id = %s
        GROUP BY c.category_name
        ORDER BY total_spent DESC
        LIMIT 1
    """, (user_id,))
    category_stats = cur.fetchone()
    
    if basic_stats:
        return {
            'total_transactions': basic_stats[0],
            'total_expenses': float(basic_stats[1]) if basic_stats[1] else 0.0,
            'largest_expense': float(basic_stats[2]) if basic_stats[2] else 0.0,
            'most_used_category': category_stats[0] if category_stats else 'None'
        }
    else:
        return {
            'total_transactions': 0,
            'total_expenses': 0.0,
            'largest_expense': 0.0,
            'most_used_category': 'None'
        }
    
    cur.close()

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        transactions = grab_user_transactions(session['user_id'])
        statistics = get_user_statistics(session['user_id'])
        
        # Get categories for the modal
        cur = mysql.connection.cursor()
        cur.execute("SELECT category_id, category_name FROM Category ORDER BY category_id")
        categories = cur.fetchall()
        cur.close()
        
        return render_template('index.html', username=session['username'], transactions=transactions, statistics=statistics, categories=categories)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        if user:
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user[0]  # user_id is the first column
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
        cur.execute("SELECT * FROM Users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            msg = "Username already exists! Please choose a different username."
            return render_template('register.html', msg=msg)
        
        # If username doesn't exist, insert new user
        cur.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        msg = "You have successfully registered, Please login to continue"
        return render_template('login.html', msg=msg)
    return render_template('register.html', msg=msg)
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# CRUD Routes for Transactions
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    date = request.form['date']
    amount = request.form['amount']
    description = request.form['description']
    category_id = request.form['category_id']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO Transactions (date, amount, description, user_id, category_id) 
        VALUES (%s, %s, %s, %s, %s)
    """, (date, amount, description, session['user_id'], category_id))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('home'))

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    transaction_id = request.form['transaction_id']
    date = request.form['date']
    amount = request.form['amount']
    description = request.form['description']
    category_id = request.form['category_id']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE Transactions 
        SET date = %s, amount = %s, description = %s, category_id = %s 
        WHERE transaction_id = %s AND user_id = %s
    """, (date, amount, description, category_id, transaction_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('home'))

@app.route('/delete_transaction', methods=['POST'])
def delete_transaction():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    transaction_id = request.form['transaction_id']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM Transactions 
        WHERE transaction_id = %s AND user_id = %s
    """, (transaction_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('home'))

@app.route('/export_csv')
def export_csv():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # TODO: Implement CSV export functionality
    return redirect(url_for('home'))

@app.route('/set_budget')
def set_budget():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # TODO: Implement budget setting functionality
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)