# Gans Scooter – City Data Engineering Pipeline

## 📌 Project Overview
Gans Scooter is a data engineering project that collects, transforms, and stores real-world data from multiple external sources into a MySQL database.
The pipeline combines web scraping and APIs to collect information about five major German cities:
Berlin
Hamburg
Munich
Frankfurt
Stuttgart
The project demonstrates an end-to-end ETL (Extract, Transform, Load) workflow using Python and MySQL.

---
🏗️ Data Pipeline Architecture
```text
                    DATA SOURCES
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Wikipedia      OpenWeather     RapidAPI
      Web Scraping       API       / AeroDataBox
          │              │              │
          │              │              │
          ▼              ▼              ▼
       Cities         Weather        Flights
     Population
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                    Python ETL
                         │
                  Extract / Transform
                         │
                         ▼
                    MySQL Database
                  ┌───────────────┐
                  │ gans_cities   │
                  │               │
                  │ cities        │
                  │ populations   │
                  │ weather       │
                  │ airports      │
                  │ flights       │
                  └───────────────┘
                         │
                         ▼
                   Data Validation
```
---
🔍 Data Sources
1. Wikipedia – Cities & Demographics
The pipeline uses Python, Requests, and BeautifulSoup to scrape city information from Wikipedia.
For each city, the pipeline collects:
City name
Country
Latitude
Longitude
Population
Date the population data was gathered
The data is stored in:
`cities`
`populations`
2. OpenWeather API – Weather Data
The pipeline uses the OpenWeather API to retrieve current weather information based on each city's latitude and longitude.
Collected information includes:
Temperature
Feels-like temperature
Rain
Wind speed
Snow
Sunrise
Sunset
Weather description
Observation datetime
The data is stored in the `weather` table.
3. RapidAPI / AeroDataBox – Flight Data
Flight information is collected through AeroDataBox via RapidAPI.
The pipeline uses the following ICAO airport codes:
City	ICAO
Berlin	EDDB
Hamburg	EDDH
Munich	EDDM
Frankfurt	EDDF
Stuttgart	EDDS
The flight pipeline collects:
Arrival airport ICAO
Departure airport ICAO
Departure airport name
Flight number
Scheduled arrival time
Data retrieval timestamp
The data is stored in the `flights` table.
---
🗄️ MySQL Database
The database is:
```text
gans_cities
```
It contains five main tables:
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
`cities`
Stores master information for each city, including geographic coordinates.
`populations`
Stores population snapshots associated with each city and collection date.
`weather`
Stores weather observations associated with each city.
`airports`
Stores the ICAO airport codes associated with each city.
`flights`
Stores arriving flight information and links flights to departure and arrival airports.

---
## ⚙️ Skills/Tools
`Programming` `Python` `SQL` `MySQL` `ETL` `Data Engineering` `Web Scraping` `REST API` `BeautifulSoup` `Requests` `OpenWeather API` `RapidAPI` `AeroDataBox API` `Data Modeling` `Database Design`

---
🔄 ETL Process
Extract
Data is extracted from three external sources:
```text
Wikipedia
OpenWeather API
RapidAPI / AeroDataBox
```
Transform
Python processes the raw data by:
Parsing HTML
Extracting relevant Wikipedia fields
Cleaning population values
Parsing geographic coordinates
Converting timestamps
Structuring API responses
Preparing records for relational storage
Load
The transformed data is loaded into MySQL:
```text
cities
populations
weather
airports
flights
```
After loading, the pipeline reads data back from MySQL to validate the stored records.
---
📂 Project Structure
```text
Gans-Scooter/
│
├── gans_scooter_pipeline.py
│
├── gans_scooter_database.sql
│
├── requirements.txt
│
├── .env.example
│
└── README.md
```
---
🚀 How to Run
1. Clone the repository
```bash
git clone <your-repository-url>
cd Gans-Scooter
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Create the MySQL database
Open the SQL file:
```text
gans_scooter_database.sql
```
Run it in MySQL Workbench or another MySQL client.
This creates the:
```text
gans_cities
```
database and all required tables.
4. Configure API keys and MySQL credentials
Copy:
```text
.env.example
```
to:
```text
.env
```
Then add your credentials:
```env
OPENWEATHER_API_KEY=your_openweather_api_key
RAPIDAPI_KEY=your_rapidapi_key

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=gans_cities
```
Do not commit `.env` to GitHub.
5. Run the pipeline
```bash
python gans_scooter_pipeline.py
```
The pipeline performs the following steps:
```text
Wikipedia
    ↓
Scrape city & population data
    ↓
MySQL
    ↓
Read city coordinates
    ↓
OpenWeather API
    ↓
Load weather data
    ↓
RapidAPI / AeroDataBox
    ↓
Load flight data
    ↓
Read data back from MySQL
    ↓
Validate results
```
---
## 🎯 Project Goals

This project demonstrates practical skills in:
Data extraction
Web scraping
REST API integration
ETL pipeline development
Data transformation
Relational database design
SQL
Python
MySQL
Foreign keys and table relationships
API integration
Error handling
Environment-variable management
Data validation

---
## 📈 Possible Future Improvements

Future versions of the pipeline could include:
Automated daily execution
Historical weather data
Historical flight data
Additional German cities
Additional airports
Logging
API retry mechanisms
Duplicate-flight detection
Data-quality checks
Docker containerization
Apache Airflow orchestration
Power BI or Tableau dashboard
Automated testing
CI/CD integration

---
🧠 Data Engineering Concepts Demonstrated
This project follows a simple but complete data engineering architecture:
```text
SOURCE
  ↓
EXTRACT
  ↓
TRANSFORM
  ↓
LOAD
  ↓
STORE
  ↓
VALIDATE
```
The project demonstrates how heterogeneous data sources can be integrated into a single relational database.
---
📊 Example Data Model
```text
                    ┌──────────────┐
                    │    CITIES    │
                    │--------------│
                    │ city_id (PK) │
                    │ city         │
                    │ country      │
                    │ latitude     │
                    │ longitude    │
                    └──────┬───────┘
                           │
              ┌────────────┼─────────────┐
              │            │             │
              ▼            ▼             ▼
      ┌─────────────┐ ┌───────────┐ ┌────────────┐
      │ POPULATIONS │ │  WEATHER  │ │  AIRPORTS  │
      │-------------│ │-----------│ │------------│
      │ city_id(FK) │ │ city_id   │ │ airport_id │
      │ population  │ │ temp      │ │ city_id(FK)│
      │ date        │ │ wind      │ │ icao       │
      └─────────────┘ │ rain      │ └─────┬──────┘
                      │ snow      │       │
                      └───────────┘       ▼
                                  ┌──────────────┐
                                  │   FLIGHTS    │
                                  │--------------│
                                  │ flight_id PK │
                                  │ arrival ICAO │
                                  │ departure    │
                                  │ flight no.   │
                                  │ arrival time │
                                  └──────────────┘
```
---
### 🔐 Security

API keys and database passwords are stored in environment variables rather than directly in the Python source code.
The `.env` file should be added to `.gitignore`:
```text
.env
```
This prevents credentials from being accidentally committed to GitHub.
