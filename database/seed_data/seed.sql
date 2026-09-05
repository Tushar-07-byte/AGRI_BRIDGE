-- =========================================
-- AGRIBRIDGE FINAL SEED DATA
-- =========================================

USE agribridge_test;


-- =========================================
-- 1. FARMERS
-- =========================================

INSERT INTO farmers (id, name) VALUES
(1, 'Ramesh'),
(2, 'Suresh'),
(3, 'Mahesh'),
(4, 'Rahul'),
(5, 'Anil');


-- =========================================
-- 2. LISTINGS
-- =========================================

INSERT INTO listings
(
    id,
    farmer_id,
    crop_type,
    photo_path,
    health_status,
    confidence,
    harvest_date,
    quantity_est,
    status
)
VALUES
(
    1,
    1,
    'Rice',
    'uploads/rice.jpg',
    'Healthy',
    0.9550,
    '2026-08-20',
    500.00,
    'Available'
),
(
    2,
    2,
    'Wheat',
    'uploads/wheat.jpg',
    'Healthy',
    0.9200,
    '2026-08-22',
    400.00,
    'Available'
),
(
    3,
    3,
    'Maize',
    'uploads/maize.jpg',
    'Healthy',
    0.8900,
    '2026-08-25',
    350.00,
    'Available'
),
(
    4,
    4,
    'Tomato',
    'uploads/tomato.jpg',
    'Healthy',
    0.9100,
    '2026-08-18',
    250.00,
    'Available'
),
(
    5,
    5,
    'Potato',
    'uploads/potato.jpg',
    'Healthy',
    0.9300,
    '2026-08-21',
    300.00,
    'Available'
);


-- =========================================
-- 3. BUYERS
-- =========================================

INSERT INTO buyers (id, name) VALUES
(101, 'Buyer One'),
(102, 'Buyer Two'),
(103, 'Buyer Three'),
(104, 'Buyer Four'),
(105, 'Buyer Five');


-- =========================================
-- 4. ORDERS
-- =========================================

INSERT INTO orders
(
    id,
    listing_id,
    buyer_id,
    committed_at
)
VALUES
(
    1,
    1,
    101,
    '2026-08-01 10:00:00'
),
(
    2,
    2,
    102,
    '2026-08-02 11:30:00'
),
(
    3,
    3,
    103,
    '2026-08-03 09:45:00'
),
(
    4,
    4,
    104,
    '2026-08-04 14:15:00'
),
(
    5,
    5,
    105,
    '2026-08-05 16:00:00'
);


-- =========================================
-- END OF AGRIBRIDGE SEED DATA
-- =========================================