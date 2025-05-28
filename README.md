# ☁ Gans Cloud Data Pipeline

Cloud-native data pipeline for ingesting weather and flight data to support scooter fleet optimization. Built as part of the WBS CODING SCHOOL Data Science Bootcamp.

## 🔧 Tech Stack

- **Google Cloud**: Cloud SQL · Cloud Functions · Cloud Scheduler  
- **Python**: Data collection and transformation  
- **MySQL**: Normalized relational schema  
- **APIs**: OpenWeatherMap & AeroDataBox  

## 📁 Project Structure

```
cloud_functions/                            # Cloud Function logic and dependencies
  ├── main.py
  ├── helper.py
  ├── requirements.txt
  ├── config.json                           # (gitignored - contains credentials)
  └── config_template.json                  # template for config setup

notebooks/                                  # Local development & testing
  ├── gans_init_static_data.ipynb
  ├── init_and_test_cloud_functions.ipynb
  ├── helper.py
  ├── config.json                           # (gitignored)
  └── config_template.json                  # template

sql/                                        # SQL schema setup
  └── gans-db_cloud_creation.sql
```

## ⚙️ Usage

### 1. Install dependencies
```bash
pip install -r cloud_functions/requirements.txt
pip install flask
```

### 2. Local Testing (via Notebook)
Open the following notebook:

```
notebooks/init_and_test_cloud_functions.ipynb
```

This notebook:
- Loads configuration from `config.json`
- Simulates an HTTP request using `flask.Request`
- Calls `add_dynamic_data()` and prints the response

### 3. Configure credentials
Copy and rename `config_template.json` → `config.json`, then add your credentials:

```json
{
  "db_config": {
    "schema": "gans",
    "host": "YOUR_CLOUD_SQL_IP",
    "user": "root",
    "password": "YOUR_PASSWORD",
    "port": 3306,
    "sql_geo_table": "geodata",
    "sql_weather_table": "weathers",
    "sql_airport_table": "airports",
    "sql_airport_code_column": "airport_icao",
    "sql_flight_table": "flights"
  },
  "api_config": {
    "weather": {
      "key": "YOUR_WEATHER_API_KEY"
    },
    "flights": {
      "host": "aerodatabox.p.rapidapi.com",
      "key": "YOUR_FLIGHTS_API_KEY",
      "decoding": "utf-8",
      "code_type": "icao",
      "delay": 2
    }
  }
}
```

> ⚠️ `config.json` is excluded from version control via `.gitignore`.

## 🕒 Automation

- Cloud Function is triggered via **Cloud Scheduler**
- Cron: `0 0 * * *` (daily at midnight CET)

---

Built during the [WBS Data Science Bootcamp](https://www.wbscodingschool.com/) (2025)
