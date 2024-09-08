-- prepares a MySQL server for the project

CREATE DATABASE IF NOT EXISTS afrigroove;
CREATE USER 'afrigroove_user'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON afrigroove.* TO 'afrigroove_user'@'localhost';
FLUSH PRIVILEGES;
