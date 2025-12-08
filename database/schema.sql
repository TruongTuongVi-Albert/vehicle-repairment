CREATE DATABASE IF NOT EXISTS car_repair_db;
USE car_repair_db;

-- Users table (Admin, Reception, Technician, Cashier)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, -- In production, use hashed passwords
    role ENUM('admin', 'reception', 'technician', 'cashier') NOT NULL,
    full_name VARCHAR(100)
);

-- Cars table
CREATE TABLE IF NOT EXISTS cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    license_plate VARCHAR(20) NOT NULL UNIQUE,
    owner_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    address VARCHAR(255),
    email VARCHAR(100)
);

-- Reception Slips (Phieu tiep nhan)
CREATE TABLE IF NOT EXISTS reception_slips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT NOT NULL,
    reception_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'waiting', 'repairing', 'completed', 'paid') DEFAULT 'pending',
    description TEXT, -- Description of the issue reported by customer
    FOREIGN KEY (car_id) REFERENCES cars(id)
);

-- Components/Parts (Vat tu/Phu tung)
CREATE TABLE IF NOT EXISTS components (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0
);

-- Repair Slips (Phieu sua chua)
CREATE TABLE IF NOT EXISTS repair_slips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reception_slip_id INT NOT NULL,
    technician_id INT,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    FOREIGN KEY (reception_slip_id) REFERENCES reception_slips(id),
    FOREIGN KEY (technician_id) REFERENCES users(id)
);

-- Repair Details (Chi tiet sua chua - items used)
CREATE TABLE IF NOT EXISTS repair_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repair_slip_id INT NOT NULL,
    component_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price_at_time DECIMAL(10, 2) NOT NULL,
    category VARCHAR(250),
    labor_fee DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (repair_slip_id) REFERENCES repair_slips(id),
    FOREIGN KEY (component_id) REFERENCES components(id)
);

-- Invoices (Hoa don)
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repair_slip_id INT NOT NULL,
    cashier_id INT,
    total_amount DECIMAL(10, 2) NOT NULL,
    vat_rate DECIMAL(5, 2) DEFAULT 10.00, -- 10%
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) DEFAULT 'cash',
    FOREIGN KEY (repair_slip_id) REFERENCES repair_slips(id),
    FOREIGN KEY (cashier_id) REFERENCES users(id)
);

-- System Settings (Quy dinh)
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255)
);

-- Insert default settings
INSERT IGNORE INTO system_settings (setting_key, setting_value) VALUES ('max_cars_per_day', '30');
INSERT IGNORE INTO system_settings (setting_key, setting_value) VALUES ('vat_rate', '10');

-- Insert default users (password: 123)
INSERT IGNORE INTO users (username, password, role, full_name) VALUES 
('admin', '123', 'admin', 'Administrator'),
('reception', '123', 'reception', 'Receptionist A'),
('tech', '123', 'technician', 'Technician B'),
('cashier', '123', 'cashier', 'Cashier C');

-- Insert sample components
INSERT IGNORE INTO components (name, current_price, stock_quantity) VALUES 
('Bugi Denso', 200000, 100),
('Nhớt Castrol', 150000, 50),
('Lốp Michelin', 2500000, 20);
