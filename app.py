from flask import Flask, render_template, request, redirect, url_for, session, g
from flask_mysqldb import MySQL
from flask_babel import Babel, gettext, ngettext, get_locale
import os
from werkzeug.utils import send_from_directory

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
        return session['language']
    # Default to English
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
        SELECT t.transaction_id, t.date, t.amount, t.description, t.user_id, c.category_name, t.category_id,
               tag.name as tag_name, tag.tag_id
        FROM Transactions t 
        INNER JOIN Category c ON t.category_id = c.category_id 
        LEFT JOIN Tags_and_Transactions tat ON t.transaction_id = tat.transaction_id
        LEFT JOIN Tags tag ON tat.tag_id = tag.tag_id
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

def get_tag_names(user_id):
    """Get all tag names for a specific user"""
    cur = mysql.connection.cursor()
    cur.execute("SELECT tag_id, name FROM Tags WHERE user_id = %s ORDER BY name", (user_id,))
    tags = cur.fetchall()
    cur.close()
    return tags

def get_user_tags_with_stats(user_id):
    """Get user's tags with statistics"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT t.tag_id, t.name, 
               COALESCE(SUM(tr.amount), 0) as total_amount,
               COUNT(tr.transaction_id) as transaction_count
        FROM Tags t
        LEFT JOIN Tags_and_Transactions tat ON t.tag_id = tat.tag_id
        LEFT JOIN Transactions tr ON tat.transaction_id = tr.transaction_id AND tr.user_id = %s
        WHERE t.user_id = %s
        GROUP BY t.tag_id, t.name
        ORDER BY total_amount DESC
    """, (user_id, user_id))
    tags = cur.fetchall()
    cur.close()
    return tags

def get_transactions_by_tag(user_id, tag_id):
    """Get all transactions for a specific tag"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT tr.transaction_id, tr.date, tr.amount, tr.description, c.category_name
        FROM Transactions tr
        INNER JOIN Tags_and_Transactions tat ON tr.transaction_id = tat.transaction_id
        INNER JOIN Category c ON tr.category_id = c.category_id
        INNER JOIN Tags t ON tat.tag_id = t.tag_id
        WHERE tr.user_id = %s AND tat.tag_id = %s AND t.user_id = %s
        ORDER BY tr.date DESC
    """, (user_id, tag_id, user_id))
    transactions = cur.fetchall()
    cur.close()
    return transactions

def check_user_balance(user_id):
    """Check if user has set their initial balance"""
    cur = mysql.connection.cursor()
    cur.execute("SELECT balance_id FROM Current_Balance WHERE user_id = %s", (user_id,))
    balance_exists = cur.fetchone()
    cur.close()
    return balance_exists is not None

def get_user_current_balance(user_id):
    """Get user's current balance (total balance minus transaction sum)"""
    cur = mysql.connection.cursor()
    
    # Get total balance
    cur.execute("SELECT amount FROM Current_Balance WHERE user_id = %s", (user_id,))
    balance_result = cur.fetchone()
    
    if not balance_result:
        return 0.0
    
    total_balance = float(balance_result[0])
    
    # Get sum of all transactions
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM Transactions WHERE user_id = %s", (user_id,))
    transaction_sum = float(cur.fetchone()[0])
    
    cur.close()
    
    # Current balance = total balance - transaction sum
    current_balance = total_balance - transaction_sum
    return current_balance

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        transactions = grab_user_transactions(session['user_id'])
        statistics = get_user_statistics(session['user_id'])
        current_balance = get_user_current_balance(session['user_id'])
        
        # Get translated categories for the modal
        categories = get_category_names()
        tags = get_tag_names(session['user_id'])
        
        return render_template('index.html', username=session.get('username', ''), transactions=transactions, statistics=statistics, categories=categories, tags=tags, current_balance=current_balance, locale=str(get_locale()))
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
            
            # Check if user has set their initial balance
            if not check_user_balance(user[0]):
                return redirect(url_for('set_initial_balance'))
            else:
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
@app.route('/set_initial_balance', methods=['GET', 'POST'])
def set_initial_balance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    msg = ""
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            if amount <= 0:
                msg = gettext("Balance must be greater than 0")
            else:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO Current_Balance (user_id, amount) VALUES (%s, %s)", 
                          (session['user_id'], amount))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('home'))
        except ValueError:
            msg = gettext("Please enter a valid amount")
    
    return render_template('set_balance.html', msg=msg, locale=str(get_locale()))

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
    tag_id = request.form.get('tag_id', '').strip()
    
    # Validate amount is greater than 0
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return redirect(url_for('home'))
    except ValueError:
        return redirect(url_for('home'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO Transactions (date, amount, description, user_id, category_id) 
        VALUES (%s, %s, %s, %s, %s)
    """, (date, amount, description, session['user_id'], category_id))
    
    # Get the transaction ID
    transaction_id = cur.lastrowid
    
    # Add tag association if tag is selected
    if tag_id:
        # Verify the tag belongs to the current user
        cur.execute("SELECT tag_id FROM Tags WHERE tag_id = %s AND user_id = %s", (tag_id, session['user_id']))
        tag_exists = cur.fetchone()
        
        if tag_exists:
            cur.execute("""
                INSERT INTO Tags_and_Transactions (tag_id, transaction_id) 
                VALUES (%s, %s)
            """, (tag_id, transaction_id))
    
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
    tag_id = request.form.get('tag_id', '').strip()
    
    # Validate amount is greater than 0
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return redirect(url_for('home'))
    except ValueError:
        return redirect(url_for('home'))
    
    cur = mysql.connection.cursor()
    
    # Update transaction
    cur.execute("""
        UPDATE Transactions 
        SET date = %s, amount = %s, description = %s, category_id = %s 
        WHERE transaction_id = %s AND user_id = %s
    """, (date, amount, description, category_id, transaction_id, session['user_id']))
    
    # Remove existing tag associations
    cur.execute("DELETE FROM Tags_and_Transactions WHERE transaction_id = %s", (transaction_id,))
    
    # Add new tag association if tag is selected
    if tag_id:
        # Verify the tag belongs to the current user
        cur.execute("SELECT tag_id FROM Tags WHERE tag_id = %s AND user_id = %s", (tag_id, session['user_id']))
        tag_exists = cur.fetchone()
        
        if tag_exists:
            cur.execute("""
                INSERT INTO Tags_and_Transactions (tag_id, transaction_id) 
                VALUES (%s, %s)
            """, (tag_id, transaction_id))
    
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

@app.route('/edit_balance', methods=['POST'])
def edit_balance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    try:
        new_balance = float(request.form['new_balance'])
        if new_balance <= 0:
            return redirect(url_for('home'))
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE Current_Balance 
            SET amount = %s 
            WHERE user_id = %s
        """, (new_balance, session['user_id']))
        mysql.connection.commit()
        cur.close()
        
    except ValueError:
        pass  # Invalid input, just redirect back
    
    return redirect(url_for('home'))

@app.route('/add_balance', methods=['POST'])
def add_balance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    try:
        amount_to_add = float(request.form['amount_to_add'])
        if amount_to_add <= 0:
            return redirect(url_for('home'))
        
        cur = mysql.connection.cursor()
        # Get current balance
        cur.execute("SELECT amount FROM Current_Balance WHERE user_id = %s", (session['user_id'],))
        current_balance = cur.fetchone()
        
        if current_balance:
            new_total_balance = float(current_balance[0]) + amount_to_add
            cur.execute("""
                UPDATE Current_Balance 
                SET amount = %s 
                WHERE user_id = %s
            """, (new_total_balance, session['user_id']))
        else:
            # If no balance exists, create one
            cur.execute("""
                INSERT INTO Current_Balance (user_id, amount) 
                VALUES (%s, %s)
            """, (session['user_id'], amount_to_add))
        
        mysql.connection.commit()
        cur.close()
        
    except ValueError:
        pass  # Invalid input, just redirect back
    
    return redirect(url_for('home'))

# Tag Management Routes
@app.route('/manage_tags')
def manage_tags():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    tags = get_user_tags_with_stats(session['user_id'])
    current_balance = get_user_current_balance(session['user_id'])
    
    # Calculate tag statistics
    tag_count = len(tags)
    total_tagged_amount = sum(tag[2] for tag in tags)
    most_used_tag = max(tags, key=lambda x: x[3])[1] if tags else None
    
    return render_template('tags.html', 
                         username=session.get('username', ''), 
                         tags=tags, 
                         tag_count=tag_count,
                         total_tagged_amount=total_tagged_amount,
                         most_used_tag=most_used_tag,
                         current_balance=current_balance,
                         locale=str(get_locale()))

@app.route('/add_tag', methods=['POST'])
def add_tag():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    tag_name = request.form['tag_name'].strip()
    
    if not tag_name:
        return redirect(url_for('manage_tags'))
    
    cur = mysql.connection.cursor()
    
    # Check if tag already exists for this user
    cur.execute("SELECT * FROM Tags WHERE name = %s AND user_id = %s", (tag_name, session['user_id']))
    existing_tag = cur.fetchone()
    
    if existing_tag:
        return redirect(url_for('manage_tags'))
    
    # Insert new tag
    cur.execute("INSERT INTO Tags (name, user_id) VALUES (%s, %s)", (tag_name, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_tags'))

@app.route('/edit_tag', methods=['POST'])
def edit_tag():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    tag_id = request.form['tag_id']
    tag_name = request.form['tag_name'].strip()
    
    if not tag_name:
        return redirect(url_for('manage_tags'))
    
    cur = mysql.connection.cursor()
    
    # Check if tag name already exists for this user (excluding current tag)
    cur.execute("SELECT * FROM Tags WHERE name = %s AND tag_id != %s AND user_id = %s", (tag_name, tag_id, session['user_id']))
    existing_tag = cur.fetchone()
    
    if existing_tag:
        return redirect(url_for('manage_tags'))
    
    # Update tag (ensure it belongs to the current user)
    cur.execute("UPDATE Tags SET name = %s WHERE tag_id = %s AND user_id = %s", (tag_name, tag_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_tags'))

@app.route('/delete_tag', methods=['POST'])
def delete_tag():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    tag_id = request.form['tag_id']
    
    cur = mysql.connection.cursor()
    
    # Delete tag associations first (only for transactions owned by this user)
    cur.execute("""
        DELETE tat FROM Tags_and_Transactions tat
        INNER JOIN Transactions tr ON tat.transaction_id = tr.transaction_id
        WHERE tat.tag_id = %s AND tr.user_id = %s
    """, (tag_id, session['user_id']))
    
    # Delete the tag (only if it belongs to the current user)
    cur.execute("DELETE FROM Tags WHERE tag_id = %s AND user_id = %s", (tag_id, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_tags'))

@app.route('/get_tag_transactions')
def get_tag_transactions():
    if 'logged_in' not in session:
        return {'error': 'Not logged in'}, 401
    
    tag_id = request.args.get('tag_id')
    if not tag_id:
        return {'error': 'Tag ID required'}, 400
    
    # Verify the tag belongs to the current user
    cur = mysql.connection.cursor()
    cur.execute("SELECT tag_id FROM Tags WHERE tag_id = %s AND user_id = %s", (tag_id, session['user_id']))
    tag_exists = cur.fetchone()
    cur.close()
    
    if not tag_exists:
        return {'error': 'Tag not found'}, 404
    
    transactions = get_transactions_by_tag(session['user_id'], tag_id)
    
    # Convert to JSON format
    transaction_list = []
    for transaction in transactions:
        transaction_list.append({
            'transaction_id': transaction[0],
            'date': str(transaction[1]),
            'amount': float(transaction[2]),
            'description': transaction[3],
            'category': transaction[4]
        })
    
    return {'transactions': transaction_list}

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)