# Expense Tracker Web Application

A Flask-based web application for tracking personal expenses with features like budget management, friend connections, and multi-language support (English/Chinese).

## Features

- User registration and authentication
- Expense tracking with categories and tags
- Budget management
- Friend connections and expense sharing
- Multi-language support (English/Chinese)
- CSV export functionality (to be added)
- Recurring transactions
- Payment method tracking (to be added)

## Prerequisites

- Python 3.7 or higher
- MySQL 8.0 or higher
- pip (Python package installer)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Database-project
```

### 2. Set Up Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. MySQL Database Setup

#### Install MySQL
- **macOS**: `brew install mysql` or download from [MySQL website](https://dev.mysql.com/downloads/mysql/)
- **Windows**: Download from [MySQL website](https://dev.mysql.com/downloads/mysql/)
- **Linux**: `sudo apt-get install mysql-server` (Ubuntu/Debian)

#### Start MySQL Service
```bash
# macOS
brew services start mysql

# Windows
# MySQL service should start automatically

# Linux
sudo systemctl start mysql
```

#### Create Database and User
```bash
# Connect to MySQL as root
mysql -u root -p

# In MySQL prompt, run:
CREATE DATABASE expenses_project;
CREATE USER 'expense_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON expenses_project.* TO 'expense_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### Import Database Schema
```bash
# Import the database structure (DDL)
mysql -u root -p expenses_project < DDL.sql

# Import sample data (DML) - optional
mysql -u root -p expenses_project < DML.sql
```

### 5. Configure Application

Edit `app.py` and update the MySQL configuration:

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # or your MySQL username
app.config['MYSQL_PASSWORD'] = 'your_password'  # your MySQL password
app.config['MYSQL_DB'] = 'expenses_project'
```

### 6. Run the Application

```bash
# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the application
flask run
```

The application will be available at `http://localhost:5000`

## Usage

1. Open your browser and go to `http://localhost:5000`
2. Register a new account or login with existing credentials
3. Set your initial balance
4. Start tracking your expenses!

## Project Structure

```
Database-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── DDL.sql               # Database structure (Data Definition Language)
├── DML.sql               # Sample data (Data Manipulation Language)
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── translations/         # Multi-language support
├── backup_scripts/       # Database backup scripts
├── babel.cfg            # Babel configuration for translations
└── messages.pot         # Translation template
```

## Troubleshooting

### Common Issues

1. **MySQL Connection Error**
   - Ensure MySQL service is running
   - Check username/password in `app.py`
   - Verify database exists

2. **Port Already in Use**
   - Change port: `flask run --port=5001`
   - Or kill process using port 5000

3. **Module Not Found Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

### Database Reset

To reset the database:
```bash
mysql -u root -p
DROP DATABASE expenses_project;
CREATE DATABASE expenses_project;
EXIT;
# Import the database structure (DDL)
mysql -u root -p expenses_project < DDL.sql
# Import sample data (DML) - optional
mysql -u root -p expenses_project < DML.sql
```

