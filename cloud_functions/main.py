# Import required packages and modules
import json
import logging
import functions_framework

# Import helper functions
from helper import load_weather_info_to_sql, load_flight_info_to_sql

# Load config
with open("config.json", "r") as f:
    config = json.load(f)
    db_config = config["db_config"]
    api_config = config["api_config"]
    print("Config loaded.")
    
@functions_framework.http
def add_dynamic_data(request):
    logging.info("Function execution started.")

    try:
        # Load weather data into SQL
        load_weather_info_to_sql(db_config, api_config)
        logging.info("Weather data successfully loaded.")

        # Load flight data into SQL
        load_flight_info_to_sql(db_config, api_config)
        logging.info("Flight data successfully loaded.")

        return "Success", 200

    except Exception as e:
        logging.exception("An error occurred during function execution:")
        return f"Error: {str(e)}", 500