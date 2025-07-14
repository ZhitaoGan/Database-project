from flask import Flask, render_template, request, redirect, url_for, session, g
from flask_mysqldb import MySQL
from flask_babel import Babel, gettext, ngettext, get_locale

app = Flask(__name__)

app.secret_key = 'your secret key'

# Enter your database sconnection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'GZTgzt1126'
app.config['MYSQL_DB'] = 'expenses_project'

# Babel configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'zh']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Initialize Babel
babel = Babel(app)

# Intialize MySQL
mysql = MySQL(app)

def get_locale():
    # Check if user has selected a language
    if 'language' in session:
        print(f"DEBUG: Session language is {session['language']}")
        return session['language']
    # Default to English
    print("DEBUG: No session language, defaulting to English")
    return 'en'

babel.init_app(app, locale_selector=get_locale)

@app.route('/set_language/<language>')
def set_language(language):
    if language in ['en', 'zh']:
        session['language'] = language
    return redirect(request.referrer or url_for('login'))

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
    
    # Get current language for default value
    current_language = get_locale()
    default_category = '无' if current_language == 'zh' else 'None'
    
    if basic_stats:
        return {
            'total_transactions': basic_stats[0],
            'total_expenses': float(basic_stats[1]) if basic_stats[1] else 0.0,
            'largest_expense': float(basic_stats[2]) if basic_stats[2] else 0.0,
            'most_used_category': category_stats[0] if category_stats else default_category
        }
    else:
        return {
            'total_transactions': 0,
            'total_expenses': 0.0,
            'largest_expense': 0.0,
            'most_used_category': default_category
        }
    
    cur.close()

def get_category_names():
    """Get category names based on current language"""
    current_language = get_locale()
    
    # Category name mapping
    category_mapping = {
        'Food & Dining': {'en': 'Food & Dining', 'zh': '餐饮美食'},
        'Transportation': {'en': 'Transportation', 'zh': '交通出行'},
        'Shopping': {'en': 'Shopping', 'zh': '购物消费'},
        'Entertainment': {'en': 'Entertainment', 'zh': '娱乐休闲'},
        'Utilities': {'en': 'Utilities', 'zh': '水电煤气'},
        'Healthcare': {'en': 'Healthcare', 'zh': '医疗健康'},
        'Education': {'en': 'Education', 'zh': '教育培训'},
        'Other': {'en': 'Other', 'zh': '其他支出'}
    }
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT category_id, category_name FROM Category ORDER BY category_id")
    categories = cur.fetchall()
    cur.close()
    
    # Translate category names
    translated_categories = []
    for category in categories:
        category_id, original_name = category
        translated_name = category_mapping.get(original_name, {}).get(current_language, original_name)
        translated_categories.append((category_id, translated_name))
    
    return translated_categories

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        transactions = grab_user_transactions(session['user_id'])
        statistics = get_user_statistics(session['user_id'])
        
        # Get translated categories for the modal
        categories = get_category_names()
        
        return render_template('index.html', username=session.get('username', ''), transactions=transactions, statistics=statistics, categories=categories, locale=str(get_locale()))
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
            msg = gettext("Invalid username or password")
    return render_template('login.html', msg=msg, locale=str(get_locale()))


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
            msg = gettext("Username already exists! Please choose a different username.")
            return render_template('register.html', msg=msg, locale=str(get_locale()))
        
        # If username doesn't exist, insert new user
        cur.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        msg = gettext("You have successfully registered, Please login to continue")
        return render_template('login.html', msg=msg, locale=str(get_locale()))
    return render_template('register.html', msg=msg, locale=str(get_locale()))
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