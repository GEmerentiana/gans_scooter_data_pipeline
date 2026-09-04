"""
Gans Scooter – City Data Engineering Pipeline

End-to-end ETL pipeline:
Wikipedia -> Python -> MySQL
OpenWeather -> Python -> MySQL
RapidAPI/AeroDataBox -> Python -> MySQL

The pipeline processes five German cities:
Berlin, Hamburg, Munich, Frankfurt and Stuttgart.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta
from typing import Any

import mysql.connector
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CITIES = {
    "Berlin": {
        "wikipedia": "https://en.wikipedia.org/wiki/Berlin",
        "icao": "EDDB",
    },
    "Hamburg": {
        "wikipedia": "https://en.wikipedia.org/wiki/Hamburg",
        "icao": "EDDH",
    },
    "Munich": {
        "wikipedia": "https://en.wikipedia.org/wiki/Munich",
        "icao": "EDDM",
    },
    "Frankfurt": {
        "wikipedia": "https://en.wikipedia.org/wiki/Frankfurt",
        "icao": "EDDF",
    },
    "Stuttgart": {
        "wikipedia": "https://en.wikipedia.org/wiki/Stuttgart",
        "icao": "EDDS",
    },
}

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "gans_cities"),
}

RAPIDAPI_HOST = "aerodatabox.p.rapidapi.com"

HTTP_TIMEOUT = 30

WIKIPEDIA_HEADERS = {
    "User-Agent": "GansScooterDataPipeline/2.0 (educational portfolio project)"
}

RAPIDAPI_HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY or "",
    "X-RapidAPI-Host": RAPIDAPI_HOST,
}


# ---------------------------------------------------------------------------
# Configuration / database
# ---------------------------------------------------------------------------

def validate_configuration() -> None:
    """Fail early when required configuration is missing."""
    required = {
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "RAPIDAPI_KEY": RAPIDAPI_KEY,
        "MYSQL_USER": MYSQL_CONFIG["user"],
        "MYSQL_DATABASE": MYSQL_CONFIG["database"],
    }

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise RuntimeError(
            "Missing configuration values: " + ", ".join(missing)
        )


def get_mysql_connection():
    """Create a MySQL connection using environment configuration."""
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except Error as exc:
        raise RuntimeError(f"MySQL connection failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Wikipedia extraction
# ---------------------------------------------------------------------------

def parse_coordinate(value: str | None) -> float | None:
    """Extract a decimal coordinate from Wikipedia text."""
    if not value:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", value)

    if not match:
        return None

    coordinate = float(match.group(0))
    upper = value.upper()

    if "S" in upper or "W" in upper:
        coordinate = -abs(coordinate)

    return coordinate


def extract_population(infobox) -> int | None:
    """Extract the first population value from the Wikipedia infobox."""
    for row in infobox.find_all("tr"):
        header = row.find("th")
        value = row.find("td")

        if not header or not value:
            continue

        key = header.get_text(" ", strip=True).lower()

        if key != "population":
            continue

        text = value.get_text(" ", strip=True)

        # Prefer a substantial integer to avoid accidentally selecting
        # a year from the surrounding text.
        candidates = re.findall(r"\d[\d,.\s]*", text)

        for raw in candidates:
            cleaned = (
                raw.replace(",", "")
                .replace(".", "")
                .replace(" ", "")
            )

            if cleaned.isdigit() and len(cleaned) >= 4:
                return int(cleaned)

    return None


def scrape_city(city_name: str, wikipedia_url: str) -> dict[str, Any]:
    """Extract city metadata and population from Wikipedia."""
    print(f"[Wikipedia] Scraping {city_name}...")

    response = requests.get(
        wikipedia_url,
        headers=WIKIPEDIA_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", class_="infobox")

    if not infobox:
        raise ValueError(f"Wikipedia infobox not found for {city_name}")

    latitude_element = soup.find(class_="latitude")
    longitude_element = soup.find(class_="longitude")

    latitude = parse_coordinate(
        latitude_element.get_text(strip=True)
        if latitude_element
        else None
    )

    longitude = parse_coordinate(
        longitude_element.get_text(strip=True)
        if longitude_element
        else None
    )

    population = extract_population(infobox)

    if population is None:
        raise ValueError(f"Population not found for {city_name}")

    result = {
        "city": city_name,
        "country": "Germany",
        "latitude": latitude,
        "longitude": longitude,
        "population": population,
        "date_gathered": date.today(),
    }

    print(
        f"  Population: {population:,} | "
        f"Coordinates: {latitude}, {longitude}"
    )

    return result


def extract_all_city_data() -> list[dict[str, Any]]:
    """Extract all configured city records."""
    records = []

    for city_name, config in CITIES.items():
        try:
            records.append(
                scrape_city(city_name, config["wikipedia"])
            )
        except Exception as exc:
            print(f"[ERROR] Wikipedia {city_name}: {exc}")

    return records


# ---------------------------------------------------------------------------
# City / population loading
# ---------------------------------------------------------------------------

def load_city_data(records: list[dict[str, Any]]) -> None:
    """Upsert city master data and daily population snapshots."""
    if not records:
        return

    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        for record in records:
            cursor.execute(
                """
                INSERT INTO cities (city, country, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    country = VALUES(country),
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude)
                """,
                (
                    record["city"],
                    record["country"],
                    record["latitude"],
                    record["longitude"],
                ),
            )

            cursor.execute(
                "SELECT city_id FROM cities WHERE city = %s",
                (record["city"],),
            )
            city_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO populations
                    (city_id, population, date_gathered)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    population = VALUES(population)
                """,
                (
                    city_id,
                    record["population"],
                    record["date_gathered"],
                ),
            )

        connection.commit()
        print(f"[MySQL] Loaded {len(records)} city records.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# OpenWeather extraction / loading
# ---------------------------------------------------------------------------

def get_weather_data(
    city_name: str,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Get current weather for a city."""
    print(f"[OpenWeather] Collecting {city_name}...")

    # Current weather endpoint is intentionally used instead of the
    # subscription-dependent One Call endpoint.
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    response = requests.get(
        url,
        params=params,
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()

    rain = data.get("rain", {}).get("1h", 0)
    snow = data.get("snow", {}).get("1h", 0)
    weather = data.get("weather", [])

    observed_at = datetime.fromtimestamp(
        data["dt"]
    )

    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
    sunset = datetime.fromtimestamp(data["sys"]["sunset"])

    result = {
        "city": city_name,
        "observation_datetime": observed_at,
        "temp": data["main"].get("temp"),
        "feels_like": data["main"].get("feels_like"),
        "rain": rain,
        "wind": data.get("wind", {}).get("speed", 0),
        "snow": snow,
        "sunrise": sunrise,
        "sunset": sunset,
        "weather_description": (
            weather[0].get("description") if weather else None
        ),
    }

    print(
        f"  {result['temp']} °C | "
        f"{result['weather_description']}"
    )

    return result


def load_weather_data() -> None:
    """Read city coordinates, fetch weather, and insert observations."""
    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT city_id, city, latitude, longitude
            FROM cities
            WHERE city IN (%s, %s, %s, %s, %s)
            """,
            tuple(CITIES.keys()),
        )
        cities = cursor.fetchall()

        inserted = 0

        for city in cities:
            if city["latitude"] is None or city["longitude"] is None:
                print(f"[WARNING] Skipping {city['city']}: missing coordinates")
                continue

            try:
                weather = get_weather_data(
                    city["city"],
                    float(city["latitude"]),
                    float(city["longitude"]),
                )

                cursor.execute(
                    """
                    INSERT INTO weather (
                        observation_datetime,
                        temp,
                        feels_like,
                        rain,
                        wind,
                        snow,
                        city_id,
                        sunrise,
                        sunset,
                        weather_description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        temp = VALUES(temp),
                        feels_like = VALUES(feels_like),
                        rain = VALUES(rain),
                        wind = VALUES(wind),
                        snow = VALUES(snow),
                        sunrise = VALUES(sunrise),
                        sunset = VALUES(sunset),
                        weather_description = VALUES(weather_description)
                    """,
                    (
                        weather["observation_datetime"],
                        weather["temp"],
                        weather["feels_like"],
                        weather["rain"],
                        weather["wind"],
                        weather["snow"],
                        city["city_id"],
                        weather["sunrise"],
                        weather["sunset"],
                        weather["weather_description"],
                    ),
                )
                inserted += 1

            except Exception as exc:
                print(f"[ERROR] Weather {city['city']}: {exc}")

        connection.commit()
        print(f"[MySQL] Weather records processed: {inserted}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# Airport loading
# ---------------------------------------------------------------------------

def load_airports() -> None:
    """Upsert the configured airport for each city."""
    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        loaded = 0

        for city_name, config in CITIES.items():
            cursor.execute(
                "SELECT city_id FROM cities WHERE city = %s",
                (city_name,),
            )
            result = cursor.fetchone()

            if not result:
                print(f"[WARNING] City not found: {city_name}")
                continue

            city_id = result[0]

            cursor.execute(
                """
                INSERT INTO airports (city_id, icao)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    city_id = VALUES(city_id)
                """,
                (city_id, config["icao"]),
            )
            loaded += 1

        connection.commit()
        print(f"[MySQL] Airport mappings processed: {loaded}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# AeroDataBox / RapidAPI extraction
# ---------------------------------------------------------------------------

def get_flight_data(
    airport_icao: str,
    target_date: date,
) -> list[dict[str, Any]]:
    """Retrieve arriving flights for one airport and date."""
    print(
        f"[RapidAPI/AeroDataBox] "
        f"Collecting arrivals for {airport_icao}..."
    )

    all_flights = []

    time_windows = [
        ("00:00", "11:59"),
        ("12:00", "23:59"),
    ]

    for start_time, end_time in time_windows:
        url = (
            "https://aerodatabox.p.rapidapi.com/"
            f"flights/airports/icao/{airport_icao}/"
            f"{target_date}T{start_time}/"
            f"{target_date}T{end_time}"
        )

        params = {
            "withLeg": "true",
            "direction": "Arrival",
            "withCancelled": "false",
            "withCodeshared": "true",
            "withCargo": "false",
            "withPrivate": "false",
            "withLocation": "false",
        }

        response = requests.get(
            url,
            headers=RAPIDAPI_HEADERS,
            params=params,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        for flight in data.get("arrivals", []):
            departure = flight.get("departure", {})
            departure_airport = departure.get("airport", {})

            arrival = flight.get("arrival", {})
            scheduled = arrival.get("scheduledTime", {})
            scheduled_local = scheduled.get("local")

            if not scheduled_local:
                continue

            all_flights.append(
                {
                    "arrival_airport_icao": airport_icao,
                    "departure_airport_icao": departure_airport.get("icao"),
                    "departure_airport_name": departure_airport.get("name"),
                    "flight_number": flight.get("number"),
                    "scheduled_arrival_time": scheduled_local,
                    "data_retrieved_at": datetime.now(),
                }
            )

    print(f"  Flights collected: {len(all_flights)}")
    return all_flights


def load_flight_data() -> None:
    """Retrieve tomorrow's arrivals and load them into MySQL."""
    target_date = date.today() + timedelta(days=1)

    print(f"[Flights] Target date: {target_date}")

    all_flights = []

    for city_name, config in CITIES.items():
        try:
            all_flights.extend(
                get_flight_data(config["icao"], target_date)
            )
        except requests.HTTPError as exc:
            print(f"[ERROR] Flight API {city_name}: {exc}")
        except Exception as exc:
            print(f"[ERROR] Flight {city_name}: {exc}")

    if not all_flights:
        print("[Flights] No flight records collected.")
        return

    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        sql = """
            INSERT INTO flights (
                arrival_airport_icao,
                departure_airport_icao,
                departure_airport_name,
                flight_number,
                scheduled_arrival_time,
                data_retrieved_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                data_retrieved_at = VALUES(data_retrieved_at),
                departure_airport_name = VALUES(departure_airport_name)
        """

        for flight in all_flights:
            cursor.execute(
                sql,
                (
                    flight["arrival_airport_icao"],
                    flight["departure_airport_icao"],
                    flight["departure_airport_name"],
                    flight["flight_number"],
                    flight["scheduled_arrival_time"],
                    flight["data_retrieved_at"],
                ),
            )

        connection.commit()
        print(f"[MySQL] Flight records processed: {len(all_flights)}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_database() -> None:
    """Run basic row-count and latest-observation checks."""
    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        tables = [
            "cities",
            "populations",
            "weather",
            "airports",
            "flights",
        ]

        print("\n[VALIDATION] Row counts")

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) AS row_count FROM {table}")
            result = cursor.fetchone()
            print(f"  {table}: {result['row_count']}")

        cursor.execute(
            """
            SELECT
                c.city,
                p.population,
                p.date_gathered
            FROM cities c
            LEFT JOIN populations p
                ON c.city_id = p.city_id
                AND p.date_gathered = (
                    SELECT MAX(p2.date_gathered)
                    FROM populations p2
                    WHERE p2.city_id = c.city_id
                )
            ORDER BY c.city
            """
        )

        print("\n[VALIDATION] Latest population snapshot")
        for row in cursor.fetchall():
            print(
                f"  {row['city']}: "
                f"{row['population']} "
                f"({row['date_gathered']})"
            )

        cursor.execute(
            """
            SELECT
                c.city,
                w.observation_datetime,
                w.temp,
                w.weather_description
            FROM weather w
            INNER JOIN cities c
                ON w.city_id = c.city_id
            INNER JOIN (
                SELECT city_id, MAX(observation_datetime) AS max_dt
                FROM weather
                GROUP BY city_id
            ) latest
                ON latest.city_id = w.city_id
                AND latest.max_dt = w.observation_datetime
            ORDER BY c.city
            """
        )

        print("\n[VALIDATION] Latest weather observation")
        for row in cursor.fetchall():
            print(
                f"  {row['city']}: "
                f"{row['temp']} °C | "
                f"{row['weather_description']} | "
                f"{row['observation_datetime']}"
            )

    finally:
        cursor.close()
        connection.close()


# ---------------------------------------------------------------------------
# Main ETL orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the complete ETL pipeline."""
    print("=" * 70)
    print("GANS SCOOTER DATA ENGINEERING PIPELINE")
    print("=" * 70)

    validate_configuration()
    print("[CONFIG] Configuration validation passed.")

    city_records = extract_all_city_data()
    load_city_data(city_records)

    load_weather_data()
    load_airports()
    load_flight_data()

    validate_database()

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
