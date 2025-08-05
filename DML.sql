-- Sample Data Insertion for Expenses Project Database
-- This file contains sample data for testing and demonstration purposes

USE `expenses_project`;

-- Insert sample users
INSERT INTO Users (username, password) VALUES 
('john_doe', 'hashed_password_123'),
('jane_smith', 'hashed_password_456'),
('mike_wilson', 'hashed_password_789'),
('sarah_jones', 'hashed_password_101'),
('alex_brown', 'hashed_password_202');

-- Insert sample friends relationships
INSERT INTO Friends (user_id, friend_id, status, request_date) VALUES 
(1, 2, 'accepted', '2024-01-15 10:30:00'),
(1, 3, 'accepted', '2024-01-20 14:45:00'),
(2, 4, 'pending', '2024-02-01 09:15:00'),
(3, 5, 'accepted', '2024-01-25 16:20:00'),
(4, 1, 'accepted', '2024-01-10 11:00:00'),
(5, 2, 'blocked', '2024-02-05 13:30:00');

-- Insert sample payment methods
INSERT INTO Payment_Methods (method_name) VALUES 
('Credit Card'),
('Debit Card'),
('Cash'),
('Bank Transfer'),
('Digital Wallet'),
('Check');

-- Insert sample tags for users
INSERT INTO Tags (name, user_id) VALUES 
('Work', 1),
('Personal', 1),
('Emergency', 1),
('Entertainment', 2),
('Food', 2),
('Transport', 2),
('Shopping', 3),
('Bills', 3),
('Health', 4),
('Education', 4),
('Travel', 5),
('Gifts', 5);

-- Insert sample transactions
INSERT INTO Transactions (date, amount, description, user_id, category_id) VALUES 
('2024-02-01', 45.50, 'Grocery shopping at Walmart', 1, 1),
('2024-02-02', 25.00, 'Gas station fill-up', 1, 2),
('2024-02-03', 120.00, 'New shoes from Nike', 1, 3),
('2024-02-04', 15.99, 'Netflix subscription', 1, 4),
('2024-02-05', 85.00, 'Electricity bill', 1, 5),
('2024-02-01', 32.75, 'Lunch at Chipotle', 2, 1),
('2024-02-02', 18.50, 'Uber ride to work', 2, 2),
('2024-02-03', 65.00, 'Movie tickets and snacks', 2, 4),
('2024-02-04', 150.00, 'Doctor appointment', 2, 6),
('2024-02-05', 45.00, 'Textbook purchase', 2, 7),
('2024-02-01', 89.99, 'Amazon purchase - headphones', 3, 3),
('2024-02-02', 35.00, 'Phone bill', 3, 5),
('2024-02-03', 22.50, 'Coffee and breakfast', 3, 1),
('2024-02-04', 75.00, 'Gym membership', 3, 6),
('2024-02-05', 12.99, 'Spotify premium', 3, 4),
('2024-02-01', 180.00, 'Dental cleaning', 4, 6),
('2024-02-02', 28.00, 'Bus pass for the month', 4, 2),
('2024-02-03', 95.00, 'Online course subscription', 4, 7),
('2024-02-04', 42.00, 'Dinner with friends', 4, 1),
('2024-02-05', 110.00, 'New jacket', 4, 3),
('2024-02-01', 55.00, 'Weekend getaway gas', 5, 2),
('2024-02-02', 200.00, 'Hotel booking', 5, 8),
('2024-02-03', 75.00, 'Restaurant dinner', 5, 1),
('2024-02-04', 30.00, 'Movie theater', 5, 4),
('2024-02-05', 125.00, 'Birthday gift for friend', 5, 8);

-- Insert sample budgets
INSERT INTO Budgets (name, amount, start_date, end_date, user_id, category_id) VALUES 
('Monthly Food Budget', 400.00, '2024-02-01', '2024-02-29', 1, 1),
('Transportation Budget', 150.00, '2024-02-01', '2024-02-29', 1, 2),
('Entertainment Budget', 200.00, '2024-02-01', '2024-02-29', 2, 4),
('Shopping Budget', 300.00, '2024-02-01', '2024-02-29', 2, 3),
('Healthcare Budget', 500.00, '2024-02-01', '2024-02-29', 3, 6),
('Education Budget', 250.00, '2024-02-01', '2024-02-29', 4, 7),
('Travel Budget', 800.00, '2024-02-01', '2024-02-29', 5, 8);

-- Insert sample recurring transactions
INSERT INTO Recurring_Transactions (amount, description, frequency, next_date, user_id, category_id) VALUES 
(15.99, 'Netflix subscription', 'monthly', '2024-03-01', 1, 4),
(85.00, 'Electricity bill', 'monthly', '2024-03-05', 1, 5),
(45.00, 'Phone bill', 'monthly', '2024-03-10', 2, 5),
(75.00, 'Gym membership', 'monthly', '2024-03-15', 3, 6),
(12.99, 'Spotify premium', 'monthly', '2024-03-01', 3, 4),
(95.00, 'Online course subscription', 'monthly', '2024-03-20', 4, 7),
(28.00, 'Bus pass', 'monthly', '2024-03-01', 4, 2);

-- Insert sample goals
INSERT INTO Goals (user_id, goal_name, target_amount, goal_type, start_date, end_date) VALUES 
(1, 'Save for vacation', 2000.00, 'yearly', '2024-01-01', '2024-12-31'),
(2, 'Emergency fund', 5000.00, 'yearly', '2024-01-01', '2024-12-31'),
(3, 'New laptop fund', 1200.00, 'yearly', '2024-01-01', '2024-12-31'),
(4, 'Student loan payment', 3000.00, 'yearly', '2024-01-01', '2024-12-31'),
(5, 'Wedding fund', 10000.00, 'yearly', '2024-01-01', '2024-12-31');

-- Insert sample current balances
INSERT INTO Current_Balance (user_id, amount) VALUES 
(1, 2500.00),
(2, 1800.50),
(3, 3200.75),
(4, 950.25),
(5, 4200.00);

-- Insert sample transaction-payment method relationships
INSERT INTO Transaction_Payment_Method (transaction_id, method_id) VALUES 
(1, 2), -- Grocery shopping with debit card
(2, 2), -- Gas with debit card
(3, 1), -- Shoes with credit card
(4, 1), -- Netflix with credit card
(5, 4), -- Electricity bill with bank transfer
(6, 2), -- Lunch with debit card
(7, 5), -- Uber with digital wallet
(8, 1), -- Movie tickets with credit card
(9, 4), -- Doctor appointment with bank transfer
(10, 1), -- Textbook with credit card
(11, 1), -- Amazon purchase with credit card
(12, 4), -- Phone bill with bank transfer
(13, 3), -- Coffee with cash
(14, 1), -- Gym membership with credit card
(15, 1), -- Spotify with credit card
(16, 4), -- Dental cleaning with bank transfer
(17, 2), -- Bus pass with debit card
(18, 1), -- Online course with credit card
(19, 2), -- Dinner with debit card
(20, 1), -- Jacket with credit card
(21, 2), -- Gas with debit card
(22, 1), -- Hotel with credit card
(23, 2), -- Restaurant with debit card
(24, 3), -- Movie with cash
(25, 1); -- Gift with credit card

-- Insert sample transaction-tag relationships
INSERT INTO Tags_and_Transactions (tag_id, transaction_id) VALUES 
(1, 1), -- Work tag for grocery shopping
(2, 3), -- Personal tag for shoes
(3, 5), -- Emergency tag for electricity bill
(4, 8), -- Entertainment tag for movie tickets
(5, 6), -- Food tag for lunch
(6, 7), -- Transport tag for Uber
(7, 11), -- Shopping tag for Amazon purchase
(8, 12), -- Bills tag for phone bill
(9, 16), -- Health tag for dental cleaning
(10, 18), -- Education tag for online course
(11, 21), -- Travel tag for gas
(11, 22), -- Travel tag for hotel
(12, 25); -- Gifts tag for birthday gift

-- Display sample data summary
SELECT 'Sample data insertion completed successfully!' as Status;
SELECT COUNT(*) as Total_Users FROM Users;
SELECT COUNT(*) as Total_Transactions FROM Transactions;
SELECT COUNT(*) as Total_Budgets FROM Budgets;
SELECT COUNT(*) as Total_Goals FROM Goals; 