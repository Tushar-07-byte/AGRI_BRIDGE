CREATE DATABASE IF NOT EXISTS agribridge_final;

USE agribridge_final;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,

    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id)
);

USE agribridge_final;

SHOW TABLES;
SELECT DATABASE();

SHOW TABLES;

SELECT DATABASE();
SHOW TABLES;

DESCRIBE farmers;
DESCRIBE listings;
DESCRIBE orders;

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'agribridge_final'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
  USE agribridge_final;

SHOW CREATE TABLE farmers;
SHOW CREATE TABLE listings;
SHOW CREATE TABLE orders;
 
 USE agribridge_final;

DESCRIBE listings;
DESCRIBE farmers;
DESCRIBE orders;

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'agribridge_final'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

USE agribridge_final;

SELECT * FROM farmers;

SELECT * FROM listings;

SELECT * FROM orders;

USE agribridge_final;

INSERT INTO farmers (id, name) VALUES
(1, 'Ramesh'),
(2, 'Suresh'),
(3, 'Mahesh'),
(4, 'Rahul'),
(5, 'Anil');

SELECT * FROM farmers;

INSERT INTO listings
(farmer_id, crop_type, photo_path, health_status, confidence, harvest_date, quantity_est)
VALUES
(1, 'Rice', 'uploads/rice.jpg', 'Healthy', 0.9550, '2026-08-15', 100.00),
(2, 'Wheat', 'uploads/wheat.jpg', 'Healthy', 0.9230, '2026-08-18', 150.00),
(3, 'Maize', 'uploads/maize.jpg', 'Healthy', 0.9420, '2026-08-20', 200.00),
(4, 'Potato', 'uploads/potato.jpg', 'Healthy', 0.9010, '2026-08-22', 120.00),
(5, 'Tomato', 'uploads/tomato.jpg', 'Healthy', 0.9640, '2026-08-25', 180.00

SELECT * FROM listings;

USE agribridge_final;

USE agribridge_final;

INSERT INTO orders
(listing_id, buyer_id, committed_at)
VALUES
(1, 101, '2026-08-01 10:00:00'),
(2, 102, '2026-08-02 11:30:00'),
(3, 103, '2026-08-03 09:45:00'),
(4, 104, '2026-08-04 14:15:00'),
(5, 105, '2026-08-05 16:00:00');

USE agribridge_final;

SELECT id, farmer_id, crop_type
FROM listings
ORDER BY id;
SELECT id, name
FROM farmers
ORDER BY id;

SELECT 
    o.id AS order_id,
    o.listing_id,
    o.buyer_id,
    o.committed_at
FROM orders o;

SELECT 
    id,
    farmer_id,
    crop_type
FROM listings
ORDER BY id;

SELECT id, farmer_id, crop_type
FROM agribridge_final.listings
ORDER BY id;

INSERT INTO orders
(listing_id, buyer_id, committed_at)
VALUES
(1, 101, '2026-08-01 10:00:00'),
(2, 102, '2026-08-02 11:30:00'),
(3, 103, '2026-08-03 09:45:00'),
(4, 104, '2026-08-04 14:15:00'),
(5, 105, '2026-08-05 16:00:00');

USE agribridge_final;

SELECT id, farmer_id, crop_type
FROM listings
ORDER BY id;

USE agribridge_final;

INSERT INTO orders
(listing_id, buyer_id, committed_at)
VALUES
(6, 101, '2026-08-01 10:00:00'),
(7, 102, '2026-08-02 11:30:00'),
(8, 103, '2026-08-03 09:45:00'),
(9, 104, '2026-08-04 14:15:00'),
(10, 105, '2026-08-05 16:00:00');
SELECT * FROM orders;

USE agribridge_final;

SELECT
    o.id AS order_id,
    o.listing_id,
    l.crop_type,
    l.farmer_id,
    f.name AS farmer_name,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;

USE agribridge_final;

-- 1. Check farmer count
SELECT COUNT(*) AS total_farmers
FROM farmers;

-- 2. Check listing count
SELECT COUNT(*) AS total_listings
FROM listings;

-- 3. Check order count
SELECT COUNT(*) AS total_orders
FROM orders;

-- 4. Check for listings without a valid farmer
SELECT l.id, l.farmer_id, l.crop_type
FROM listings l
LEFT JOIN farmers f ON l.farmer_id = f.id
WHERE f.id IS NULL;

-- 5. Check for orders without a valid listing
SELECT 
    o.id, o.listing_id
FROM
    orders o
        LEFT JOIN
    listings l ON o.listing_id = l.id
WHERE
    l.id IS NULL;
    
    USE agribridge_final;

-- 1. Show all available crop listings
SELECT
    l.id AS listing_id,
    f.name AS farmer_name,
    l.crop_type,
    l.health_status,
    l.quantity_est,
    l.harvest_date
FROM listings l
JOIN farmers f ON l.farmer_id = f.id
ORDER BY l.id;

-- 2. Show all orders with farmer and crop information
SELECT
    o.id AS order_id,
    f.name AS farmer_name,
    l.crop_type,
    l.quantity_est,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;

-- 3. Count listings by crop
SELECT
    crop_type,
    COUNT(*) AS total_listings
FROM listings
GROUP BY crop_type;

-- 4. Count orders by listing
SELECT
    listing_id,
    COUNT(*) AS total_orders
FROM orders
GROUP BY listing_id;

USE agribridge_final;

-- 1. Show all available crop listings
SELECT
    l.id AS listing_id,
    f.name AS farmer_name,
    l.crop_type,
    l.health_status,
    l.quantity_est,
    l.harvest_date
FROM listings l
JOIN farmers f ON l.farmer_id = f.id
ORDER BY l.id;

-- 2. Show all orders with farmer and crop information
SELECT
    o.id AS order_id,
    f.name AS farmer_name,
    l.crop_type,
    l.quantity_est,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;

-- 3. Count listings by crop
SELECT
    crop_type,
    COUNT(*) AS total_listings
FROM listings
GROUP BY crop_type;


SELECT
    listing_id,
    COUNT(*) AS total_orders
FROM orders
GROUP BY listing_id;

-- 4. Count orders by listing
SELECT
    listing_id,
    COUNT(*) AS total_orders
FROM orders
GROUP BY listing_id;
USE agribridge_final;

SHOW TABLES;

SELECT * FROM farmers;

SELECT * FROM listings;

SELECT * FROM orders;

SELECT
    o.id AS order_id,
    o.listing_id,
    l.crop_type,
    l.farmer_id,
    f.name AS farmer_name,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;

USE agribridge_final;

SELECT
    (SELECT COUNT(*) FROM farmers) AS farmers,
    (SELECT COUNT(*) FROM listings) AS listings,
    (SELECT COUNT(*) FROM orders) AS orders;
    
    SELECT
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'agribridge_final'
AND REFERENCED_TABLE_NAME IS NOT NULL;

USE agribridge_test;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,

    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id)
);

USE agribridge_test;

SHOW TABLES;

USE agribridge_test;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,
    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id)
);

SHOW TABLES;
USE agribridge_test;

SHOW TABLES;

USE agribridge_test;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,
    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id)
);

SHOW TABLES;

USE agribridge_test;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

USE agribridge_test;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

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

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    buyer_id INT NOT NULL,
    committed_at DATETIME,
    CONSTRAINT fk_orders_listing
        FOREIGN KEY (listing_id)
        REFERENCES listings(id)
);

SHOW TABLES;

USE agribridge_test;

INSERT INTO farmers (id, name) VALUES
(1, 'Ramesh'),
(2, 'Suresh'),
(3, 'Mahesh'),
(4, 'Rahul'),
(5, 'Anil');

INSERT INTO listings
(farmer_id, crop_type, photo_path, health_status, confidence, harvest_date, quantity_est)
VALUES
(1, 'Rice', 'uploads/rice.jpg', 'Healthy', 0.9550, '2026-08-15', 100.00),
(2, 'Wheat', 'uploads/wheat.jpg', 'Healthy', 0.9230, '2026-08-18', 150.00),
(3, 'Maize', 'uploads/maize.jpg', 'Healthy', 0.9420, '2026-08-20', 200.00),
(4, 'Potato', 'uploads/potato.jpg', 'Healthy', 0.9010, '2026-08-22', 120.00),
(5, 'Tomato', 'uploads/tomato.jpg', 'Healthy', 0.9640, '2026-08-25', 180.00);

INSERT INTO orders
(listing_id, buyer_id, committed_at)
SELECT
    l.id,
    x.buyer_id,
    x.committed_at
FROM listings l
JOIN (
    SELECT 1 AS farmer_id, 101 AS buyer_id, '2026-08-01 10:00:00' AS committed_at
    UNION ALL
    SELECT 2, 102, '2026-08-02 11:30:00'
    UNION ALL
    SELECT 3, 103, '2026-08-03 09:45:00'
    UNION ALL
    SELECT 4, 104, '2026-08-04 14:15:00'
    UNION ALL
    SELECT 5, 105, '2026-08-05 16:00:00'
) x
ON l.farmer_id = x.farmer_id;

USE agribridge_test;

SELECT COUNT(*) AS farmers FROM farmers;
SELECT COUNT(*) AS listings FROM listings;
SELECT COUNT(*) AS orders FROM orders;

INSERT INTO farmers (id, name) VALUES
(1, 'Ramesh'),
(2, 'Suresh'),
(3, 'Mahesh'),
(4, 'Rahul'),
(5, 'Anil');

INSERT INTO listings
(farmer_id, crop_type, photo_path, health_status, confidence, harvest_date, quantity_est)
VALUES
(1, 'Rice', 'uploads/rice.jpg', 'Healthy', 0.9550, '2026-08-15', 100.00),
(2, 'Wheat', 'uploads/wheat.jpg', 'Healthy', 0.9230, '2026-08-18', 150.00),
(3, 'Maize', 'uploads/maize.jpg', 'Healthy', 0.9420, '2026-08-20', 200.00),
(4, 'Potato', 'uploads/potato.jpg', 'Healthy', 0.9010, '2026-08-22', 120.00),
(5, 'Tomato', 'uploads/tomato.jpg', 'Healthy', 0.9640, '2026-08-25', 180.00);

INSERT INTO orders
(listing_id, buyer_id, committed_at)
SELECT
    l.id,
    x.buyer_id,
    x.committed_at
FROM listings l
JOIN (
    SELECT 1 AS farmer_id, 101 AS buyer_id, '2026-08-01 10:00:00' AS committed_at
    UNION ALL
    SELECT 2, 102, '2026-08-02 11:30:00'
    UNION ALL
    SELECT 3, 103, '2026-08-03 09:45:00'
    UNION ALL
    SELECT 4, 104, '2026-08-04 14:15:00'
    UNION ALL
    SELECT 5, 105, '2026-08-05 16:00:00'
) x ON l.farmer_id = x.farmer_id;



USE agribridge_test;

SELECT COUNT(*) AS total_farmers FROM farmers;
SELECT COUNT(*) AS total_listings FROM listings;
SELECT COUNT(*) AS total_orders FROM orders;

USE agribridge_test;

SELECT * FROM farmers;
SELECT * FROM listings;
SELECT * FROM orders;

USE agribridge_test;

SELECT
    l.id AS listing_id,
    f.name AS farmer_name,
    l.crop_type,
    l.health_status,
    l.quantity_est,
    l.harvest_date
FROM listings l
JOIN farmers f ON l.farmer_id = f.id
ORDER BY l.id;

SELECT
    o.id AS order_id,
    f.name AS farmer_name,
    l.crop_type,
    l.quantity_est,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;


USE agribridge_test;

SELECT
    (SELECT COUNT(*) FROM farmers) AS total_farmers,
    (SELECT COUNT(*) FROM listings) AS total_listings,
    (SELECT COUNT(*) FROM orders) AS total_orders;
    
    USE agribridge_test;

SELECT
    l.id AS listing_id,
    l.farmer_id
FROM listings l
LEFT JOIN farmers f ON l.farmer_id = f.id
WHERE f.id IS NULL;

SELECT
    o.id AS order_id,
    o.listing_id
FROM orders o
LEFT JOIN listings l ON o.listing_id = l.id
WHERE l.id IS NULL;

USE agribridge_test;

SELECT
    o.id AS order_id,
    f.name AS farmer_name,
    l.crop_type,
    l.quantity_est,
    o.buyer_id,
    o.committed_at
FROM orders o
JOIN listings l ON o.listing_id = l.id
JOIN farmers f ON l.farmer_id = f.id
ORDER BY o.id;

-- =========================================
-- STEP 12: ER DIAGRAM RELATIONSHIP VERIFICATION
-- AGRIBRIDGE PROJECT
-- =========================================

USE agribridge_test;

-- 1. Check all tables
SHOW TABLES;


-- 2. FARMERS → LISTINGS
-- Verify that every listing belongs to a valid farmer

SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
ORDER BY f.id;


-- 3. LISTINGS → ORDERS
-- Verify that every order belongs to a valid listing

SELECT
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    o.committed_at
FROM listings l
JOIN orders o
    ON l.id = o.listing_id
ORDER BY l.id;

SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    o.committed_at
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
JOIN orders o
    ON l.id = o.listing_id
ORDER BY f.id;


-- 4. COMPLETE ER RELATIONSHIP
-- FARMERS → LISTINGS → ORDERS

SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    o.committed_at
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
JOIN orders o
    ON l.id = o.listing_id
ORDER BY f.id;


-- 5. CHECK INVALID FARMER REFERENCES

SELECT
    l.id AS listing_id,
    l.farmer_id
FROM listings l
LEFT JOIN farmers f
    ON l.farmer_id = f.id
WHERE f.id IS NULL;


-- 6. CHECK INVALID LISTING REFERENCES

SELECT
    o.id AS order_id,
    o.listing_id
FROM orders o
LEFT JOIN listings l
    ON o.listing_id = l.id
WHERE l.id IS NULL;


-- 7. FINAL RECORD COUNT

SELECT
    (SELECT COUNT(*) FROM farmers) AS total_farmers,
    (SELECT COUNT(*) FROM listings) AS total_listings,
    (SELECT COUNT(*) FROM orders) AS total_orders;
    
    SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    o.committed_at
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
JOIN orders o
    ON l.id = o.listing_id
ORDER BY f.id;

SELECT
    l.id AS listing_id,
    l.farmer_id
FROM listings l
LEFT JOIN farmers f
    ON l.farmer_id = f.id
WHERE f.id IS NULL;

    o.id AS order_id,
    o.listing_id
FROM orders o
LEFT JOIN listings l
    ON o.listing_id = l.id
WHERE l.id IS NULL;

SELECT
    (SELECT COUNT(*) FROM farmers) AS total_farmers,
    (SELECT COUNT(*) FROM listings) AS total_listings,
    (SELECT COUNT(*) FROM orders) AS total_orders;
    
    
    USE agribridge_test;

-- COMPLETE ER RELATIONSHIP VERIFICATION

-- 1. Farmers → Listings → Orders
SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    o.committed_at
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
JOIN orders o
    ON l.id = o.listing_id
ORDER BY f.id;

-- 2. Check invalid farmer references
SELECT
    l.id AS listing_id,
    l.farmer_id
FROM listings l
LEFT JOIN farmers f
    ON l.farmer_id = f.id
WHERE f.id IS NULL;

-- 3. Check invalid listing references
SELECT
    o.id AS order_id,
    o.listing_id
FROM orders o
LEFT JOIN listings l
    ON o.listing_id = l.id
WHERE l.id IS NULL;

-- 4. Final record counts
SELECT
    (SELECT COUNT(*) FROM farmers) AS total_farmers,
    (SELECT COUNT(*) FROM listings) AS total_listings,
    (SELECT COUNT(*) FROM orders) AS total_orders;
    
    USE agribridge_test;

CREATE TABLE IF NOT EXISTS buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

INSERT INTO buyers (id, name) VALUES
(101, 'Buyer One'),
(102, 'Buyer Two'),
(103, 'Buyer Three'),
(104, 'Buyer Four'),
(105, 'Buyer Five');

ALTER TABLE orders
ADD CONSTRAINT fk_orders_buyer
FOREIGN KEY (buyer_id) REFERENCES buyers(id);

-- =========================================
-- AGRIBRIDGE BUYERS & FINAL VERIFICATION
-- =========================================

USE agribridge_test;

-- Check buyers
SELECT * FROM buyers;

-- Check Orders → Buyers relationship
SELECT
    o.id AS order_id,
    o.buyer_id,
    b.name AS buyer_name,
    o.committed_at
FROM orders o
JOIN buyers b
    ON o.buyer_id = b.id
ORDER BY o.id;

-- Check for invalid buyer references
SELECT
    o.id AS order_id,
    o.buyer_id
FROM orders o
LEFT JOIN buyers b
    ON o.buyer_id = b.id
WHERE b.id IS NULL;

-- Final record counts
SELECT
    (SELECT COUNT(*) FROM farmers) AS total_farmers,
    (SELECT COUNT(*) FROM listings) AS total_listings,
    (SELECT COUNT(*) FROM buyers) AS total_buyers,
    (SELECT COUNT(*) FROM orders) AS total_orders;

-- Final Farmer → Listing → Order ← Buyer JOIN
SELECT
    f.id AS farmer_id,
    f.name AS farmer_name,
    l.id AS listing_id,
    l.crop_type,
    o.id AS order_id,
    o.buyer_id,
    b.name AS buyer_name,
    o.committed_at
FROM farmers f
JOIN listings l
    ON f.id = l.farmer_id
JOIN orders o
    ON l.id = o.listing_id
JOIN buyers b
    ON o.buyer_id = b.id
ORDER BY f.id;