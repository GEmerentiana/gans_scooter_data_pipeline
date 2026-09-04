-- ============================================================
-- GANS SCOOTER DATA PIPELINE
-- MySQL database schema + validation queries
--
-- Sources:
--   Wikipedia       -> cities / populations
--   OpenWeather     -> weather
--   RapidAPI /
--   AeroDataBox     -> flights
--
-- IMPORTANT:
-- This script recreates the gans_cities database.
-- ============================================================

DROP DATABASE IF EXISTS gans_cities;
CREATE DATABASE gans_cities
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gans_cities;

-- ============================================================
-- 1. CITIES
-- ============================================================

CREATE TABLE cities (
    city_id INT AUTO_INCREMENT,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),

    PRIMARY KEY (city_id),
    UNIQUE KEY uq_cities_city (city)
) ENGINE=InnoDB;

-- ============================================================
-- 2. POPULATION SNAPSHOTS
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
        ON DELETE CASCADE,

    CONSTRAINT chk_population_positive
        CHECK (population > 0)
) ENGINE=InnoDB;

-- ============================================================
-- 3. WEATHER
-- ============================================================

CREATE TABLE weather (
    weather_id INT AUTO_INCREMENT,
    observation_datetime DATETIME NOT NULL,
    temp DECIMAL(6,2),
    feels_like DECIMAL(6,2),
    rain DECIMAL(8,2) DEFAULT 0,
    wind DECIMAL(8,2) DEFAULT 0,
    snow DECIMAL(8,2) DEFAULT 0,
    city_id INT NOT NULL,
    sunrise DATETIME,
    sunset DATETIME,
    weather_description VARCHAR(150),

    PRIMARY KEY (weather_id),

    CONSTRAINT fk_weather_city
        FOREIGN KEY (city_id)
        REFERENCES cities(city_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE KEY uq_weather_city_observation
        (city_id, observation_datetime),

    INDEX idx_weather_city_datetime
        (city_id, observation_datetime)
) ENGINE=InnoDB;

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
        ON DELETE CASCADE,

    CONSTRAINT chk_airport_icao
        CHECK (CHAR_LENGTH(icao) = 4)
) ENGINE=InnoDB;

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
    data_retrieved_at DATETIME NOT NULL,

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

    -- Prevent repeated loading of the same flight/time snapshot.
    UNIQUE KEY uq_flight_record (
        arrival_airport_icao,
        departure_airport_icao,
        flight_number,
        scheduled_arrival_time
    ),

    INDEX idx_flights_arrival_time
        (arrival_airport_icao, scheduled_arrival_time),

    INDEX idx_flights_retrieved_at
        (data_retrieved_at)
) ENGINE=InnoDB;

-- ============================================================
-- 6. REFERENCE DATA
-- ============================================================
-- The pipeline normally creates these records automatically.
-- These inserts are useful for an initial schema test.

INSERT INTO cities (city, country, latitude, longitude)
VALUES
    ('Berlin', 'Germany', 52.520008, 13.404954),
    ('Hamburg', 'Germany', 53.551086, 9.993682),
    ('Munich', 'Germany', 48.137154, 11.576124),
    ('Frankfurt', 'Germany', 50.110924, 8.682127),
    ('Stuttgart', 'Germany', 48.775846, 9.182932)
ON DUPLICATE KEY UPDATE
    country = VALUES(country),
    latitude = VALUES(latitude),
    longitude = VALUES(longitude);

INSERT INTO airports (city_id, icao)
SELECT city_id, 'EDDB' FROM cities WHERE city = 'Berlin'
ON DUPLICATE KEY UPDATE city_id = VALUES(city_id);

INSERT INTO airports (city_id, icao)
SELECT city_id, 'EDDH' FROM cities WHERE city = 'Hamburg'
ON DUPLICATE KEY UPDATE city_id = VALUES(city_id);

INSERT INTO airports (city_id, icao)
SELECT city_id, 'EDDM' FROM cities WHERE city = 'Munich'
ON DUPLICATE KEY UPDATE city_id = VALUES(city_id);

INSERT INTO airports (city_id, icao)
SELECT city_id, 'EDDF' FROM cities WHERE city = 'Frankfurt'
ON DUPLICATE KEY UPDATE city_id = VALUES(city_id);

INSERT INTO airports (city_id, icao)
SELECT city_id, 'EDDS' FROM cities WHERE city = 'Stuttgart'
ON DUPLICATE KEY UPDATE city_id = VALUES(city_id);

-- ============================================================
-- 7. VALIDATION QUERIES
-- ============================================================

-- A. Row counts
SELECT 'cities' AS table_name, COUNT(*) AS row_count FROM cities
UNION ALL
SELECT 'populations', COUNT(*) FROM populations
UNION ALL
SELECT 'weather', COUNT(*) FROM weather
UNION ALL
SELECT 'airports', COUNT(*) FROM airports
UNION ALL
SELECT 'flights', COUNT(*) FROM flights;

-- B. City master data
SELECT
    city_id,
    city,
    country,
    latitude,
    longitude
FROM cities
ORDER BY city;

-- C. Latest population snapshot per city
SELECT
    c.city,
    p.population,
    p.date_gathered
FROM cities c
LEFT JOIN populations p
    ON p.city_id = c.city_id
WHERE p.date_gathered IS NULL
   OR p.date_gathered = (
        SELECT MAX(p2.date_gathered)
        FROM populations p2
        WHERE p2.city_id = c.city_id
   )
ORDER BY c.city;

-- D. Latest weather observation per city
SELECT
    c.city,
    w.observation_datetime,
    w.temp,
    w.feels_like,
    w.rain,
    w.wind,
    w.snow,
    w.weather_description
FROM weather w
JOIN cities c
    ON c.city_id = w.city_id
JOIN (
    SELECT city_id, MAX(observation_datetime) AS max_dt
    FROM weather
    GROUP BY city_id
) latest
    ON latest.city_id = w.city_id
   AND latest.max_dt = w.observation_datetime
ORDER BY c.city;

-- E. Airport mapping
SELECT
    c.city,
    a.icao
FROM airports a
JOIN cities c
    ON c.city_id = a.city_id
ORDER BY c.city;

-- F. Recent flights
SELECT
    f.flight_number,
    f.departure_airport_icao,
    f.departure_airport_name,
    f.arrival_airport_icao,
    f.scheduled_arrival_time,
    f.data_retrieved_at
FROM flights f
ORDER BY f.scheduled_arrival_time;

-- G. Flight volume by destination airport
SELECT
    arrival_airport_icao,
    COUNT(*) AS flight_count
FROM flights
GROUP BY arrival_airport_icao
ORDER BY flight_count DESC;

-- H. Data-quality check: missing city coordinates
SELECT
    city,
    country
FROM cities
WHERE latitude IS NULL
   OR longitude IS NULL;

-- I. Data-quality check: invalid population values
SELECT *
FROM populations
WHERE population <= 0;

-- J. Data-quality check: missing flight numbers
SELECT
    COUNT(*) AS missing_flight_numbers
FROM flights
WHERE flight_number IS NULL
   OR TRIM(flight_number) = '';

-- K. Database relationships
SELECT
    c.city,
    COUNT(DISTINCT p.date_gathered) AS population_snapshots,
    COUNT(DISTINCT w.weather_id) AS weather_observations,
    COUNT(DISTINCT a.airport_id) AS airports
FROM cities c
LEFT JOIN populations p
    ON p.city_id = c.city_id
LEFT JOIN weather w
    ON w.city_id = c.city_id
LEFT JOIN airports a
    ON a.city_id = c.city_id
GROUP BY c.city_id, c.city
ORDER BY c.city;
