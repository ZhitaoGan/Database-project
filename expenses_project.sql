-- Create database
CREATE DATABASE IF NOT EXISTS `expenses_project` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `expenses_project`;

-- Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    CONSTRAINT PK_Users PRIMARY KEY (user_id),
    CONSTRAINT UQ_Users_username UNIQUE (username)
);

-- Friends table
CREATE TABLE IF NOT EXISTS Friends (
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    status ENUM('pending', 'accepted', 'blocked') DEFAULT 'pending',
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_Friends PRIMARY KEY (user_id, friend_id),
    CONSTRAINT FK_Friends_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT FK_Friends_friend FOREIGN KEY (friend_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT CK_Friends_not_self CHECK (user_id <> friend_id)
);

-- Category table
CREATE TABLE IF NOT EXISTS Category (
    category_id INT NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT PK_Category PRIMARY KEY (category_id),
    CONSTRAINT UQ_Category_name UNIQUE (category_name)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INT NOT NULL AUTO_INCREMENT,
    date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    CONSTRAINT PK_Transactions PRIMARY KEY (transaction_id),
    CONSTRAINT FK_Transactions_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT FK_Transactions_category FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE,
    CONSTRAINT CK_Transactions_amount_nonneg CHECK (amount >= 0)
);

-- Budgets table
CREATE TABLE IF NOT EXISTS Budgets (
    budget_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    CONSTRAINT PK_Budgets PRIMARY KEY (budget_id),
    CONSTRAINT FK_Budgets_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT FK_Budgets_category FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE,
    CONSTRAINT CK_Budgets_amount_nonneg CHECK (amount >= 0),
    CONSTRAINT CK_Budgets_date_valid CHECK (start_date <= end_date)
);

-- Recurring Transactions table
CREATE TABLE IF NOT EXISTS Recurring_Transactions (
    recurring_id INT NOT NULL AUTO_INCREMENT,
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    frequency ENUM('daily', 'weekly', 'monthly', 'yearly') NOT NULL,
    next_date DATE NOT NULL,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    CONSTRAINT PK_Recurring_Transactions PRIMARY KEY (recurring_id),
    CONSTRAINT FK_Recurring_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT FK_Recurring_category FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE,
    CONSTRAINT CK_Recurring_amount_nonneg CHECK (amount >= 0)
);

-- Tags table
CREATE TABLE IF NOT EXISTS Tags (
    tag_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    CONSTRAINT PK_Tags PRIMARY KEY (tag_id),
    CONSTRAINT FK_Tags_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT UQ_Tags_user_name UNIQUE (user_id, name)
);

-- Tags and Transactions (many-to-many)
CREATE TABLE IF NOT EXISTS Tags_and_Transactions (
    tag_id INT NOT NULL,
    transaction_id INT NOT NULL,
    CONSTRAINT PK_Tags_Transactions PRIMARY KEY (tag_id, transaction_id),
    CONSTRAINT FK_Tag_Transaction_tag FOREIGN KEY (tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE,
    CONSTRAINT FK_Tag_Transaction_transaction FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id) ON DELETE CASCADE
);

-- Payment Methods table
CREATE TABLE IF NOT EXISTS Payment_Methods (
    method_id INT NOT NULL AUTO_INCREMENT,
    method_name VARCHAR(50) NOT NULL,
    CONSTRAINT PK_Payment_Methods PRIMARY KEY (method_id),
    CONSTRAINT UQ_Payment_Methods_name UNIQUE (method_name)
);

-- Transactions and Payment Methods (many-to-many)
CREATE TABLE IF NOT EXISTS Transaction_Payment_Method (
    transaction_id INT NOT NULL,
    method_id INT NOT NULL,
    CONSTRAINT PK_Transaction_Payment_Method PRIMARY KEY (transaction_id, method_id),
    CONSTRAINT FK_Transaction_Method_transaction FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id) ON DELETE CASCADE,
    CONSTRAINT FK_Transaction_Method_method FOREIGN KEY (method_id) REFERENCES Payment_Methods(method_id) ON DELETE CASCADE
);

-- Goals table
CREATE TABLE IF NOT EXISTS Goals (
    goal_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    goal_name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(10,2) NOT NULL,
    goal_type ENUM('monthly', 'yearly') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_Goals PRIMARY KEY (goal_id),
    CONSTRAINT FK_Goals_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT CK_Goals_amount_nonneg CHECK (target_amount >= 0),
    CONSTRAINT CK_Goals_date_valid CHECK (start_date <= end_date)
);

-- Current Balance table
CREATE TABLE IF NOT EXISTS Current_Balance (
    balance_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT PK_Current_Balance PRIMARY KEY (balance_id),
    CONSTRAINT FK_Current_Balance_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT UQ_Current_Balance_user UNIQUE (user_id),
    CONSTRAINT CK_Current_Balance_amount_nonneg CHECK (amount >= 0)
);

-- Insert default categories
INSERT INTO Category (category_name, description) VALUES 
('Food & Dining', 'Restaurants, groceries, and food delivery'),
('Transportation', 'Gas, public transit, rideshare, and vehicle maintenance'),
('Shopping', 'Clothing, electronics, and general retail purchases'),
('Entertainment', 'Movies, games, concerts, and leisure activities'),
('Utilities', 'Electricity, water, gas, internet, and phone bills'),
('Healthcare', 'Medical expenses, prescriptions, and health insurance'),
('Education', 'Tuition, books, courses, and educational materials'),
('Other', 'Miscellaneous expenses not covered by other categories')
ON DUPLICATE KEY UPDATE category_name = category_name;

-- Note: Tags are now user-specific and will be created by users as needed
-- No default tags are inserted since they need to be associated with specific users
