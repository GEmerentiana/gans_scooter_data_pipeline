# Gans Scooter – City Data Engineering Pipeline

An end-to-end **Python + SQL ETL pipeline** that combines heterogeneous external data sources for five major German cities and stores the transformed data in a relational MySQL database.

The project demonstrates practical data-engineering skills: **web scraping, REST APIs, data transformation, relational modelling, ETL orchestration, error handling, environment-variable management, and data validation**.

## Project scope

The pipeline currently covers:

- Berlin
- Hamburg
- Munich
- Frankfurt
- Stuttgart

For each city, it collects:

1. **City and population data** from Wikipedia
2. **Current weather data** from OpenWeather
3. **Airport information** for the selected city airports
4. **Arriving flight data** from AeroDataBox through RapidAPI
5. **Validation results** from MySQL after loading

## Architecture

```text
                    EXTERNAL SOURCES
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
      Wikipedia      OpenWeather     RapidAPI
      Web Scraping       API        / AeroDataBox
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                  Python ETL Pipeline
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Extract     Transform     Load
                         │
                         ▼
                    MySQL Database
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Cities      Weather      Airports
             │                         │
             ▼                         ▼
       Populations                  Flights
                         │
                         ▼
                    SQL Validation
```

## Data sources

### 1. Wikipedia

Python `requests` and `BeautifulSoup` are used to extract:

- city
- country
- latitude
- longitude
- population
- population collection date

Population data is stored as a **snapshot**, so the database can support future historical population observations.

### 2. OpenWeather

The pipeline uses the OpenWeather current-weather endpoint and stores:

- observation timestamp
- temperature
- feels-like temperature
- rain in the last hour
- wind speed
- snow in the last hour
- sunrise
- sunset
- weather description

Weather observations are linked to the corresponding city through a foreign key.

### 3. AeroDataBox via RapidAPI

The flight step retrieves arriving flights for:

| City | Airport |
|---|---|
| Berlin | EDDB |
| Hamburg | EDDH |
| Munich | EDDM |
| Frankfurt | EDDF |
| Stuttgart | EDDS |

The pipeline retrieves **tomorrow's arrivals**, using `Europe/Berlin` for the target date.

Stored flight fields include:

- arrival airport ICAO
- departure airport ICAO
- departure airport name
- flight number
- scheduled arrival time
- retrieval timestamp

## Database model

Database: `gans_cities`

```text
cities
  │
  ├── populations
  │
  ├── weather
  │
  └── airports
         │
         └── flights
```

### Tables

**cities**
- `city_id` – primary key
- `city`
- `country`
- `latitude`
- `longitude`

**populations**
- `city_id` – foreign key
- `population`
- `date_gathered`
- composite primary key prevents duplicate snapshots for the same city/date

**weather**
- `weather_id` – primary key
- `observation_datetime`
- weather measurements
- `city_id` – foreign key
- unique city/timestamp constraint helps prevent duplicate observations

**airports**
- `airport_id` – primary key
- `city_id` – foreign key
- `icao` – unique airport identifier

**flights**
- `flight_id` – primary key
- arrival/departure airport ICAO
- departure airport name
- flight number
- scheduled arrival time
- retrieval timestamp
- indexes support airport/time analysis

## Repository structure

```text
gans_scooter_data_pipeline/
│
├── README.md
├── gans_scooter_data_pipeline.py
├── gans_scooter_database.sql
├── gans_scooter_data_pipeline.ipynb
├── requirements.txt
└── .env.example
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/GEmerentiana/gans_scooter_data_pipeline.git
cd gans_scooter_data_pipeline
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Recommended `requirements.txt`:

```text
requests
beautifulsoup4
mysql-connector-python
python-dotenv
```

## Configuration

Create a `.env` file in the project root:

```text
OPENWEATHER_API_KEY=your_openweather_api_key
RAPIDAPI_KEY=your_rapidapi_key

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=gans_cities
```

Never commit `.env` to GitHub.

## Create the database

Run:

```bash
mysql -u root -p < gans_scooter_database.sql
```

Or open `gans_scooter_database.sql` in MySQL Workbench and execute it.

> The SQL script recreates the `gans_cities` schema. Do not run it against a database containing data you want to keep.

## Run the ETL pipeline

```bash
python gans_scooter_data_pipeline.py
```

The pipeline runs:

```text
1. Validate configuration
        ↓
2. Scrape city + population data
        ↓
3. Load cities/populations
        ↓
4. Load current weather
        ↓
5. Load airport mappings
        ↓
6. Retrieve tomorrow's flight arrivals
        ↓
7. Load flight records
        ↓
8. Run database validation
```

The script is designed to continue processing other cities when an individual external request fails, while clearly reporting the error.

## SQL validation

The SQL file includes validation queries for:

- row counts by table
- city/population records
- weather observations
- airport mappings
- flight records
- flights grouped by destination airport
- latest weather observation per city
- duplicate checks

These queries make the project easier to demonstrate in a portfolio or technical interview.

## Important API notes

The pipeline requires valid API credentials and depends on the current availability and terms of the external services.

Because flight information is time-sensitive, results will change between pipeline runs.

The pipeline stores **retrieval timestamps** so that users can distinguish the scheduled flight time from the time at which the API data was collected.

## Data-engineering practices demonstrated

- ETL architecture
- API integration
- web scraping
- relational database design
- primary and foreign keys
- indexes and uniqueness constraints
- parameterized SQL
- transaction handling
- environment variables
- timezone-aware date handling
- HTTP timeouts
- API error handling
- data validation
- reproducible local setup

## Future improvements

Potential production-oriented extensions:

- automated daily execution
- historical weather collection
- historical flight snapshots
- structured logging
- API retry with exponential backoff
- incremental loading
- stronger flight deduplication using API identifiers
- automated data-quality tests
- Docker
- Apache Airflow
- cloud database deployment
- dashboarding with Power BI, Tableau, or Looker Studio
- CI/CD with GitHub Actions

## Portfolio value

This project is intended to demonstrate the complete path from **external data source → extraction → transformation → relational storage → validation**.

It is especially useful as a portfolio example because it combines multiple data formats and source types rather than relying on a single static CSV file.
