-- =========================================
-- AGRIBRIDGE FINAL DATABASE SCHEMA
-- Database Engineer
-- =========================================

CREATE DATABASE IF NOT EXISTS agribridge_test;
USE agribridge_test;


-- =========================================
-- 1. FARMERS TABLE
-- =========================================

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);


-- =========================================
-- 2. LISTINGS TABLE
-- =========================================

CREATE TABLE listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    photo_path VARCHAR(255),
    health_status VARCHAR(100),
    confidence DECIMAL(5,4),
    harvest_date DATE,
    quantity_est DECIMAL(10,2),
    status VARCHAR(50),

    CONSTRAINT fk_listings_farmer
        FOREIGN KEY (farmer_id)
        REFERENCES farmers(id)
);


-- =========================================
-- 3. BUYERS TABLE
-- =========================================

CREATE TABLE buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);


-- =========================================
-- 4. ORDERS TABLE
-- =========================================

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,

    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id),

    CONSTRAINT fk_orders_buyer
        FOREIGN KEY (buyer_id)
        REFERENCES buyers(id)
);


-- =========================================
-- END OF AGRIBRIDGE SCHEMA
-- =========================================