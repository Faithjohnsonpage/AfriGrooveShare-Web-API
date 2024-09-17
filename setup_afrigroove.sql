-- Prepares a MySQL server for the project (development environment)
CREATE DATABASE IF NOT EXISTS afrigroove;
CREATE USER 'afrigroove_user'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON afrigroove.* TO 'afrigroove_user'@'localhost';

-- Prepares a MySQL server for the project (testing environment)
CREATE DATABASE IF NOT EXISTS afrigroove_test;
CREATE USER 'afrigroove_test_user'@'localhost' IDENTIFIED BY 'testpassword';
GRANT ALL PRIVILEGES ON afrigroove_test.* TO 'afrigroove_test_user'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;
