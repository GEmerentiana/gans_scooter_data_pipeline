-- ============================================================
-- GANS SCOOTER DATA PIPELINE
-- MySQL database schema
-- Data sources:
--   1. Wikipedia      -> cities / populations
--   2. OpenWeather    -> weather
--   3. RapidAPI /
--      AeroDataBox    -> flights
-- ============================================================

DROP SCHEMA IF EXISTS gans_cities;

CREATE SCHEMA gans_cities;

USE gans_cities;


-- ============================================================
-- 1. CITIES
-- ============================================================

CREATE TABLE cities (
    city_id INT AUTO_INCREMENT,
    city VARCHAR(255) NOT NULL,
    country VARCHAR(255),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),

    PRIMARY KEY (city_id),

    UNIQUE KEY uq_cities_city (city)
);


-- ============================================================
-- 2. POPULATIONS
-- ============================================================

CREATE TABLE populations (
    city_id INT NOT NULL,
    population INT NOT NULL,
    date_gathered DATE NOT NULL,

    PRIMARY KEY (city_id, date_gathered),

    CONSTRAINT fk_populations_city
        FOREIGN KEY (city_id)
        REFERENCES cities(city_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 3. WEATHER
-- ============================================================

CREATE TABLE weather (
    weather_id INT AUTO_INCREMENT,
    observation_datetime DATETIME NOT NULL,
    temp DECIMAL(6,2),
    feels_like DECIMAL(6,2),
    rain DECIMAL(8,2),
    wind DECIMAL(8,2),
    snow DECIMAL(8,2),
    city_id INT NOT NULL,
    sunrise DATETIME,
    sunset DATETIME,
    weather_description VARCHAR(100),

    PRIMARY KEY (weather_id),

    CONSTRAINT fk_weather_city
        FOREIGN KEY (city_id)
        REFERENCES cities(city_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    INDEX idx_weather_city_datetime
        (city_id, observation_datetime)
);


-- ============================================================
-- 4. AIRPORTS
-- ============================================================

CREATE TABLE airports (
    airport_id INT AUTO_INCREMENT,
    city_id INT NOT NULL,
    icao CHAR(4) NOT NULL,

    PRIMARY KEY (airport_id),

    UNIQUE KEY uq_airports_icao (icao),

    CONSTRAINT fk_airports_city
        FOREIGN KEY (city_id)
        REFERENCES cities(city_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 5. FLIGHTS
-- ============================================================

CREATE TABLE flights (
    flight_id INT AUTO_INCREMENT,
    arrival_airport_icao CHAR(4),
    departure_airport_icao CHAR(4),
    departure_airport_name VARCHAR(255),
    flight_number VARCHAR(50),
    scheduled_arrival_time DATETIME,
    data_retrieved_at DATETIME,

    PRIMARY KEY (flight_id),

    CONSTRAINT fk_flights_arrival_airport
        FOREIGN KEY (arrival_airport_icao)
        REFERENCES airports(icao)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_flights_departure_airport
        FOREIGN KEY (departure_airport_icao)
        REFERENCES airports(icao)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    INDEX idx_flights_arrival_time
        (arrival_airport_icao, scheduled_arrival_time)
);


-- ============================================================
-- 6. VALIDATION QUERIES
-- ============================================================

SELECT * FROM cities;

SELECT * FROM populations;

SELECT * FROM weather;

SELECT * FROM airports;

SELECT * FROM flights;


-- ============================================================
-- 7. PIPELINE CHECK
-- ============================================================

SELECT
    c.city,
    c.country,
    c.latitude,
    c.longitude,
    p.population,
    p.date_gathered
FROM cities AS c
LEFT JOIN populations AS p
    ON c.city_id = p.city_id
ORDER BY c.city;


SELECT
    c.city,
    w.observation_datetime,
    w.temp,
    w.feels_like,
    w.rain,
    w.wind,
    w.snow,
    w.weather_description
FROM weather AS w
INNER JOIN cities AS c
    ON w.city_id = c.city_id
ORDER BY w.observation_datetime DESC;


SELECT
    f.flight_number,
    f.departure_airport_icao,
    f.departure_airport_name,
    f.arrival_airport_icao,
    f.scheduled_arrival_time,
    f.data_retrieved_at
FROM flights AS f
ORDER BY f.scheduled_arrival_time;
