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
    
    # First, get all transactions with their basic info
    cur.execute("""
        SELECT t.transaction_id, t.date, t.amount, t.description, t.user_id, c.category_name, t.category_id
        FROM Transactions t 
        INNER JOIN Category c ON t.category_id = c.category_id 
        WHERE t.user_id = %s 
        ORDER BY t.date DESC
    """, (user_id,))
    
    transactions = cur.fetchall()
    
    # For each transaction, get its tags
    result = []
    for transaction in transactions:
        transaction_id = transaction[0]
        
        # Get tags for this transaction
        cur.execute("""
            SELECT tag.name, tag.tag_id
            FROM Tags tag
            INNER JOIN Tags_and_Transactions tat ON tag.tag_id = tat.tag_id
            WHERE tat.transaction_id = %s AND tag.user_id = %s
            ORDER BY tag.name
        """, (transaction_id, user_id))
        
        tags = cur.fetchall()
        
        # Create tag names string and tag IDs string
        tag_names = ', '.join([tag[0] for tag in tags]) if tags else None
        tag_ids = ', '.join([str(tag[1]) for tag in tags]) if tags else None
        
        # Add tag info to transaction
        transaction_with_tags = transaction + (tag_names, tag_ids)
        result.append(transaction_with_tags)
    
    cur.close()
    return result

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

def process_recurring_transactions():
    """Process recurring transactions and create new transactions"""
    from datetime import date, timedelta
    
    cur = mysql.connection.cursor()
    today = date.today()
    
    # Get all recurring transactions that are due
    cur.execute("""
        SELECT recurring_id, amount, description, frequency, next_date, user_id, category_id
        FROM Recurring_Transactions 
        WHERE next_date <= %s
    """, (today,))
    
    recurring_transactions = cur.fetchall()
    
    for recurring in recurring_transactions:
        recurring_id, amount, description, frequency, next_date, user_id, category_id = recurring
        
        # Create the transaction
        cur.execute("""
            INSERT INTO Transactions (date, amount, description, user_id, category_id) 
            VALUES (%s, %s, %s, %s, %s)
        """, (next_date, amount, description, user_id, category_id))
        
        # Calculate next date based on frequency
        if frequency == 'daily':
            new_next_date = next_date + timedelta(days=1)
        elif frequency == 'weekly':
            new_next_date = next_date + timedelta(weeks=1)
        elif frequency == 'monthly':
            # Add one month (simplified calculation)
            if next_date.month == 12:
                new_next_date = next_date.replace(year=next_date.year + 1, month=1)
            else:
                new_next_date = next_date.replace(month=next_date.month + 1)
        elif frequency == 'yearly':
            new_next_date = next_date.replace(year=next_date.year + 1)
        
        # Update the next_date for this recurring transaction
        cur.execute("""
            UPDATE Recurring_Transactions 
            SET next_date = %s 
            WHERE recurring_id = %s
        """, (new_next_date, recurring_id))
    
    mysql.connection.commit()
    cur.close()

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' in session:
        # Process any due recurring transactions
        process_recurring_transactions()
        
        transactions = grab_user_transactions(session['user_id'])
        statistics = get_user_statistics(session['user_id'])
        current_balance = get_user_current_balance(session['user_id'])
        
        # Get translated categories for the modal
        categories = get_category_names()
        tags = get_tag_names(session['user_id'])
        
        from datetime import date
        today_date = date.today().isoformat()
        return render_template('index.html', username=session.get('username', ''), transactions=transactions, statistics=statistics, categories=categories, tags=tags, current_balance=current_balance, locale=str(get_locale()), today_date=today_date)
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
    tag_ids = request.form.getlist('tag_ids')  # Get multiple tag IDs
    is_recurring = request.form.get('is_recurring', 'no')
    
    # Validate amount is greater than 0
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return redirect(url_for('home'))
    except ValueError:
        return redirect(url_for('home'))
    
    cur = mysql.connection.cursor()
    
    # Add the transaction
    cur.execute("""
        INSERT INTO Transactions (date, amount, description, user_id, category_id) 
        VALUES (%s, %s, %s, %s, %s)
    """, (date, amount, description, session['user_id'], category_id))
    
    # Get the transaction ID
    transaction_id = cur.lastrowid
    
    # Add tag associations if tags are selected
    if tag_ids:
        # Verify all tags belong to the current user
        for tag_id in tag_ids:
            cur.execute("SELECT tag_id FROM Tags WHERE tag_id = %s AND user_id = %s", (tag_id, session['user_id']))
            tag_exists = cur.fetchone()
            
            if tag_exists:
                cur.execute("""
                    INSERT INTO Tags_and_Transactions (tag_id, transaction_id) 
                    VALUES (%s, %s)
                """, (tag_id, transaction_id))
    
    # If this is a recurring transaction, add it to Recurring_Transactions
    if is_recurring == 'yes':
        frequency = request.form.get('frequency', 'monthly')
        next_date = request.form.get('next_date', date)
        
        cur.execute("""
            INSERT INTO Recurring_Transactions (amount, description, frequency, next_date, user_id, category_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (amount, description, frequency, next_date, session['user_id'], category_id))
    
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
    tag_ids = request.form.getlist('tag_ids')  # Get multiple tag IDs
    
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
    
    # Add new tag associations if tags are selected
    if tag_ids:
        # Verify all tags belong to the current user
        for tag_id in tag_ids:
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

@app.route('/manage_budgets')
def manage_budgets():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    budgets = get_user_budgets_with_stats(session['user_id'])
    categories = get_category_names()
    current_balance = get_user_current_balance(session['user_id'])
    
    # Calculate budget statistics
    budget_count = len(budgets)
    total_budget_amount = sum(float(budget[2]) for budget in budgets) if budgets else 0.0
    total_spent = sum(float(budget[6]) for budget in budgets) if budgets else 0.0
    overall_progress = (total_spent / total_budget_amount * 100) if total_budget_amount > 0 else 0.0
    
    return render_template('budgets.html', 
                         username=session.get('username', ''), 
                         budgets=budgets, 
                         categories=categories,
                         budget_count=budget_count,
                         total_budget_amount=total_budget_amount,
                         total_spent=total_spent,
                         overall_progress=overall_progress,
                         current_balance=current_balance,
                         locale=str(get_locale()))

def get_user_budgets_with_stats(user_id):
    """Get user's budgets with spending statistics"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.budget_id, b.name, b.amount, b.start_date, b.end_date, c.category_name,
               COALESCE(SUM(t.amount), 0) as total_spent,
               (b.amount - COALESCE(SUM(t.amount), 0)) as remaining,
               (COALESCE(SUM(t.amount), 0) / b.amount * 100) as progress_percentage
        FROM Budgets b
        INNER JOIN Category c ON b.category_id = c.category_id
        LEFT JOIN Transactions t ON b.category_id = t.category_id 
            AND t.user_id = %s 
            AND t.date BETWEEN b.start_date AND b.end_date
        WHERE b.user_id = %s
        GROUP BY b.budget_id, b.name, b.amount, b.start_date, b.end_date, c.category_name
        ORDER BY b.start_date DESC
    """, (user_id, user_id))
    budgets = cur.fetchall()
    cur.close()
    return budgets

@app.route('/add_budget', methods=['POST'])
def add_budget():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    budget_name = request.form['budget_name'].strip()
    category_id = request.form['category_id']
    amount = request.form['amount']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    # Validate amount is greater than 0
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return redirect(url_for('manage_budgets'))
    except ValueError:
        return redirect(url_for('manage_budgets'))
    
    # Validate dates
    if start_date >= end_date:
        return redirect(url_for('manage_budgets'))
    
    cur = mysql.connection.cursor()
    
    # Check if budget already exists for this category and period
    cur.execute("""
        SELECT * FROM Budgets 
        WHERE user_id = %s AND category_id = %s 
        AND ((start_date <= %s AND end_date >= %s) OR (start_date <= %s AND end_date >= %s))
    """, (session['user_id'], category_id, start_date, start_date, end_date, end_date))
    existing_budget = cur.fetchone()
    
    if existing_budget:
        return redirect(url_for('manage_budgets'))
    
    # Insert new budget
    cur.execute("""
        INSERT INTO Budgets (name, amount, start_date, end_date, user_id, category_id) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (budget_name, amount, start_date, end_date, session['user_id'], category_id))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_budgets'))

@app.route('/edit_budget', methods=['POST'])
def edit_budget():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    budget_id = request.form['budget_id']
    budget_name = request.form['budget_name'].strip()
    category_id = request.form['category_id']
    amount = request.form['amount']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    # Validate amount is greater than 0
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return redirect(url_for('manage_budgets'))
    except ValueError:
        return redirect(url_for('manage_budgets'))
    
    # Validate dates
    if start_date >= end_date:
        return redirect(url_for('manage_budgets'))
    
    cur = mysql.connection.cursor()
    
    # Check if budget already exists for this category and period (excluding current budget)
    cur.execute("""
        SELECT * FROM Budgets 
        WHERE user_id = %s AND category_id = %s AND budget_id != %s
        AND ((start_date <= %s AND end_date >= %s) OR (start_date <= %s AND end_date >= %s))
    """, (session['user_id'], category_id, budget_id, start_date, start_date, end_date, end_date))
    existing_budget = cur.fetchone()
    
    if existing_budget:
        return redirect(url_for('manage_budgets'))
    
    # Update budget
    cur.execute("""
        UPDATE Budgets 
        SET name = %s, amount = %s, start_date = %s, end_date = %s, category_id = %s 
        WHERE budget_id = %s AND user_id = %s
    """, (budget_name, amount, start_date, end_date, category_id, budget_id, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_budgets'))

@app.route('/delete_budget', methods=['POST'])
def delete_budget():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    budget_id = request.form['budget_id']
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Budgets WHERE budget_id = %s AND user_id = %s", (budget_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_budgets'))

@app.route('/manage_friends')
def manage_friends():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    friends = get_user_friends_with_stats(session['user_id'])
    current_balance = get_user_current_balance(session['user_id'])
    
    # Calculate friend statistics
    accepted_friends_count = len([f for f in friends if f[2] == 'accepted'])
    pending_requests_count = len([f for f in friends if f[2] == 'pending'])
    avg_friend_expenses = sum(float(f[3]) for f in friends if f[2] == 'accepted') / accepted_friends_count if accepted_friends_count > 0 else 0.0
    
    return render_template('friends.html', 
                         username=session.get('username', ''), 
                         friends=friends, 
                         accepted_friends_count=accepted_friends_count,
                         pending_requests_count=pending_requests_count,
                         avg_friend_expenses=avg_friend_expenses,
                         current_balance=current_balance,
                         locale=str(get_locale()))

def get_user_friends_with_stats(user_id):
    """Get user's friends with their expense statistics"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            CASE 
                WHEN f.user_id = %s THEN f.friend_id
                ELSE f.user_id
            END as friend_id,
            u.username,
            f.status,
            COALESCE(SUM(t.amount), 0) as total_expenses,
            COUNT(t.transaction_id) as transaction_count,
            (SELECT c.category_name 
             FROM Transactions t2 
             INNER JOIN Category c ON t2.category_id = c.category_id 
             WHERE t2.user_id = CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END
             GROUP BY c.category_name 
             ORDER BY COUNT(*) DESC 
             LIMIT 1) as most_used_category,
            CASE 
                WHEN f.user_id = %s THEN 'sent'
                ELSE 'received'
            END as request_direction
        FROM Friends f
        INNER JOIN Users u ON (CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END) = u.user_id
        LEFT JOIN Transactions t ON (CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END) = t.user_id
        WHERE f.user_id = %s OR f.friend_id = %s
        GROUP BY f.user_id, f.friend_id, f.status, u.username
        ORDER BY f.status, u.username
    """, (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    friends = cur.fetchall()
    cur.close()
    return friends

@app.route('/add_friend', methods=['POST'])
def add_friend():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    friend_username = request.form['friend_username'].strip()
    
    if not friend_username:
        return redirect(url_for('manage_friends'))
    
    cur = mysql.connection.cursor()
    
    # Check if friend exists
    cur.execute("SELECT user_id FROM Users WHERE username = %s", (friend_username,))
    friend_user = cur.fetchone()
    
    if not friend_user:
        return redirect(url_for('manage_friends'))
    
    friend_id = friend_user[0]
    
    # Check if already friends or request exists
    cur.execute("""
        SELECT * FROM Friends 
        WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
    """, (session['user_id'], friend_id, friend_id, session['user_id']))
    existing_friendship = cur.fetchone()
    
    if existing_friendship:
        return redirect(url_for('manage_friends'))
    
    # Add friend request
    cur.execute("""
        INSERT INTO Friends (user_id, friend_id, status) 
        VALUES (%s, %s, 'pending')
    """, (session['user_id'], friend_id))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_friends'))

@app.route('/respond_to_friend_request', methods=['POST'])
def respond_to_friend_request():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    friend_id = request.form['friend_id']
    action = request.form['action']
    
    cur = mysql.connection.cursor()
    
    if action == 'accept':
        # Update the friend request to accepted
        cur.execute("""
            UPDATE Friends 
            SET status = 'accepted' 
            WHERE user_id = %s AND friend_id = %s
        """, (friend_id, session['user_id']))
    elif action == 'reject':
        # Delete the friend request
        cur.execute("""
            DELETE FROM Friends 
            WHERE user_id = %s AND friend_id = %s
        """, (friend_id, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_friends'))

@app.route('/remove_friend', methods=['POST'])
def remove_friend():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    friend_id = request.form['friend_id']
    
    cur = mysql.connection.cursor()
    
    # Remove the friendship (both directions)
    cur.execute("""
        DELETE FROM Friends 
        WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
    """, (session['user_id'], friend_id, friend_id, session['user_id']))
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('manage_friends'))

@app.route('/view_friend/<int:friend_id>')
def view_friend(friend_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Verify friendship exists and is accepted
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT status FROM Friends 
        WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
    """, (session['user_id'], friend_id, friend_id, session['user_id']))
    friendship = cur.fetchone()
    
    if not friendship or friendship[0] != 'accepted':
        return redirect(url_for('manage_friends'))
    
    # Get friend's username
    cur.execute("SELECT username FROM Users WHERE user_id = %s", (friend_id,))
    friend_user = cur.fetchone()
    friend_name = friend_user[0] if friend_user else 'Unknown'
    
    # Get friend's transactions
    friend_transactions = grab_user_transactions(friend_id)
    
    # Get friend's statistics
    friend_stats = get_user_statistics(friend_id)
    
    # Add additional statistics
    from datetime import date, timedelta
    today = date.today()
    first_day_month = today.replace(day=1)
    last_month = (first_day_month - timedelta(days=1)).replace(day=1)
    
    # This month expenses
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM Transactions 
        WHERE user_id = %s AND date >= %s
    """, (friend_id, first_day_month))
    this_month = float(cur.fetchone()[0])
    
    # Last month expenses
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM Transactions 
        WHERE user_id = %s AND date >= %s AND date < %s
    """, (friend_id, last_month, first_day_month))
    last_month_expenses = float(cur.fetchone()[0])
    
    # Average transaction
    avg_transaction = friend_stats['total_expenses'] / friend_stats['total_transactions'] if friend_stats['total_transactions'] > 0 else 0.0
    
    friend_stats.update({
        'this_month': this_month,
        'last_month': last_month_expenses,
        'avg_transaction': avg_transaction
    })
    
    cur.close()
    
    current_balance = get_user_current_balance(session['user_id'])
    
    return render_template('friend_detail.html',
                         username=session.get('username', ''),
                         friend_name=friend_name,
                         friend_transactions=friend_transactions,
                         friend_stats=friend_stats,
                         current_balance=current_balance,
                         locale=str(get_locale()))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)