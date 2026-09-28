-- Run this once in MySQL (e.g. `mysql -u root -p < database/create_database.sql`)
-- Creates the database used by the backend. Tables themselves are created
-- automatically by the FastAPI app / seed.py via SQLAlchemy.

CREATE DATABASE IF NOT EXISTS statsaksham
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Optional: create a dedicated application user instead of using root.
-- CREATE USER IF NOT EXISTS 'statsaksham_app'@'localhost' IDENTIFIED BY 'change_me';
-- GRANT ALL PRIVILEGES ON statsaksham.* TO 'statsaksham_app'@'localhost';
-- FLUSH PRIVILEGES;
