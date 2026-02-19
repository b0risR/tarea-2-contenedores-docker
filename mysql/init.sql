CREATE DATABASE IF NOT EXISTS datos;
USE datos;

CREATE TABLE IF NOT EXISTS coches_electricos (
    County TEXT,
    City TEXT,
    State TEXT,
    Year INT,
    Model TEXT,
    Electric_Range INT,
    Electric_Utility TEXT
);