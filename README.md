# Gans Scooter – City Data Engineering Pipeline

An end-to-end Python + SQL ETL pipeline that integrates heterogeneous external data sources for five major German cities and stores the transformed data in a relational MySQL database.
The project demonstrates practical data-engineering skills including web scraping, REST API integration, data transformation, relational database design, ETL orchestration, error handling, environment-variable management, idempotent loading, and data validation.

## Project scope
The pipeline currently covers:
* Berlin
* Hamburg
* Munich
* Frankfurt
* Stuttgart

### It collects:
City and population data from Wikipedia
Current weather data from OpenWeather
Airport reference data for the five configured city airports
Tomorrow's arriving flights from AeroDataBox through RapidAPI
Validation results from MySQL after loading

## Architecture
```text
                    EXTERNAL DATA SOURCES
          ┌──────────────┼────────────────┐
          │              │                │
          ▼              ▼                ▼
      Wikipedia      OpenWeather      RapidAPI
      Web Scraping       API         / AeroDataBox
          │              │                │
          └──────────────┼────────────────┘
                         ▼
                 Python ETL Pipeline
                         │
              ┌──────────┼───────────┐
              ▼          ▼           ▼
           Extract    Transform     Load
                                      │
                                      ▼
                                MySQL Database
                                      │
              ┌───────────────────────┼────────────────┐
              ▼                       ▼                ▼
           Cities                  Weather          Airports
              │                                        │
              ▼                                        ▼
        Populations                                  Flights
                                      │
                                      ▼
                                SQL Validation
```
## Data sources
#### 1. Wikipedia
Python `requests` and `BeautifulSoup` are used to extract:
* city
* country
* latitude
* longitude
* population
* population collection date
Population values are stored as daily snapshots, allowing future historical observations.

#### 2. OpenWeather
The pipeline uses the OpenWeather current weather endpoint and stores:
* observation timestamp
* temperature
* feels-like temperature
* rain in the last hour
* wind speed
* snow in the last hour
* sunrise
* sunset
* weather description
Weather timestamps are stored in UTC in the database.

#### 3. AeroDataBox via RapidAPI
The flight step retrieves tomorrow's arrivals for:

City	ICAO
Berlin	EDDB
Hamburg	EDDH
Munich	EDDM
Frankfurt	EDDF
Stuttgart	EDDS


The target date is calculated using the `Europe/Berlin` timezone.
Stored flight fields include:
* arrival airport ICAO
* departure airport ICAO
* departure airport name
* flight number
* scheduled arrival time
* retrieval timestamp
The pipeline requests non-codeshare arrivals to reduce duplicate representations of the same flight.

## Database model
### Database: `gans_cities`
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
### `cities`

Master city data:
* `city_id` – primary key
* `city`
* `country`
* `latitude`
* `longitude`

### `populations`
Population snapshots:
* `city_id` – foreign key
* `population`
* `date_gathered`
composite primary key prevents duplicate city/date snapshots

### `weather`
Weather observations:
* `weather_id` – primary key
* `observation_datetime`
* temperature and weather measurements
* `city_id` – foreign key
* unique `(city_id, observation_datetime)` constraint prevents duplicate observations

### `airports`
Reference airport data:
* `airport_id` – primary key
* `city_id` – foreign key
* `icao` – unique airport identifier

### `flights`
Arriving flight data:
* `flight_id` – primary key
* `arrival_airport_icao` – foreign key to the configured arrival-airport dimension
* `departure_airport_icao`
* `departure_airport_name`
* `flight_number`
* `scheduled_arrival_time`
* `data_retrieved_at`
The departure ICAO is intentionally not a foreign key because arriving flights can originate from airports outside the five-city airport reference table.
A composite uniqueness constraint supports idempotent loading of the same arrival/departure/flight/time record.

## Repository structure
```text
gans_scooter_data_pipeline/
│
├── README.md
├── gans_scooter_data_pipeline.py
├── gans_scooter_data_pipeline.ipynb
├── gans_scooter_database.sql
├── requirements.txt
├── .env.example
└── .gitignore
```
## Installation
1. Clone the repository
```bash
git clone https://github.com/GEmerentiana/gans_scooter_data_pipeline.git
cd gans_scooter_data_pipeline
```
2. Create a virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Windows Command Prompt:
```cmd
python -m venv .venv
.venv\Scripts\activate
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
## Configuration
Create a `.env` file in the project root by copying `.env.example`.
Example:
```text
OPENWEATHER_API_KEY=your_openweather_api_key
RAPIDAPI_KEY=your_rapidapi_key

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=gans_cities
```
Never commit `.env` or API keys to GitHub.

## Create the database
The SQL script creates the complete `gans_cities` schema.
MySQL CLI
```bash
mysql -u root -p < gans_scooter_database.sql
```
MySQL Workbench
Open `gans_scooter_database.sql` and execute the script.
> **Important:** the SQL file recreates the `gans_cities` database. It contains `DROP DATABASE IF EXISTS gans_cities`, so do not run it against a database containing data you want to keep.
The SQL script also inserts the five initial city and airport reference records and includes validation queries.

## Run the ETL pipeline
```bash
python gans_scooter_data_pipeline.py
```
The pipeline executes:
```text
1. Validate configuration
        ↓
2. Scrape city + population data
        ↓
3. Load cities and population snapshots
        ↓
4. Read city coordinates
        ↓
5. Retrieve current weather
        ↓
6. Load weather observations
        ↓
7. Load airport mappings
        ↓
8. Retrieve tomorrow's flight arrivals
        ↓
9. Load flight records
        ↓
10. Validate database contents
```
The pipeline uses transactions and parameterized SQL statements. Individual external requests are handled with timeouts and reported errors so that one failed city/API request does not automatically stop all other city processing.

## Notebook
`gans_scooter_data_pipeline.ipynb` provides an interactive/documentation version of the same ETL workflow.
Use the notebook when you want to:
* execute the pipeline step by step
* inspect extracted data
* demonstrate transformations
* show SQL validation results
* explain the project during a portfolio presentation or interview
Use `gans_scooter_data_pipeline.py` as the reusable standalone ETL script.

## SQL validation
The SQL file includes checks for:
* row counts
* city master data
* latest population snapshot per city
* latest weather observation per cit
* airport mappings
* flight records
* duplicate flight records
* flight counts by arrival airport
These checks make it easier to verify the pipeline after execution.

## Data-engineering practices demonstrated
* ETL architecture
* web scraping
* REST API integration
* Python data transformation
* relational database modelling
* primary and foreign keys
* indexes
* uniqueness constraint
* parameterized SQL
* transaction handling
* environment-variable management
* API timeouts
* error handling
* idempotent loading
* UTC timestamp storage
* validation and quality checks
* reproducible local setup

## Limitations
This is a portfolio project rather than a production system.
* Wikipedia page structure can change and may require parser updates.
* API availability, quotas, pricing, and response formats can change.
* Flight data is time-sensitive and will differ between runs.
* The project currently loads current weather rather than a full historical weather series.
* Flight history is not archived as immutable daily snapshots.
* No scheduler or orchestration platform is included yet.

## Future improvements
Possible production-oriented extensions:
* automated daily execution
* structured logging
* API retry with exponential backoff
* historical weather collection
* historical flight snapshots
* stronger flight deduplication using provider-specific identifiers
* automated data-quality tests
* Docker
* Apache Airflow
* cloud database deployment
* Power BI, Tableau, or Looker Studio dashboard
* GitHub Actions CI/CD

## Portfolio value
This project demonstrates the complete data flow:
External source → Extract → Transform → Load → Store → Validate
It is especially useful as a portfolio example because it integrates web-scraped data, API data, relational modelling, and validation in one reproducible ETL workflow.
