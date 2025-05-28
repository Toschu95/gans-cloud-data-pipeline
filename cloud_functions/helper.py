import pandas as pd
import requests
import http.client
import json
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

### -------- GENERAL -------- ###

def create_connection_string(schema: str, host: str, user: str, password: str, port: str) -> str:
    """Builds connection string for SQL connection."""
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'

def query_column_as_list_from_sql(connection_string: str, sql_table: str, column: str) -> list:
    """Queries column of relevant table from SQL database."""
    df = pd.read_sql(f"SELECT {column} FROM {sql_table}", con=connection_string)
    return df[column].dropna().unique().tolist()

def clear_sql_table(connection_string: str, sql_table: str) -> None:
    """Clears sql table incl. auto increment but keeps structure."""
    engine = create_engine(connection_string)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {sql_table}"))

def send_to_sql(df: pd.DataFrame, connection_string: str, sql_table: str) -> None:
    """ Sends flight table to sql."""
    df.to_sql(sql_table, if_exists='append', con=connection_string, index=False)

### -------- WEATHER -------- ###

def get_weather_responses(city_data: pd.DataFrame, api_key: str) -> dict:
    """ Retrieve weather information via api."""
    responses = {}

    for city_id, city_lat, city_lon in city_data:
        url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={city_lat}&lon={city_lon}&appid={api_key}&units=metric"
        )
        responses[city_id] = requests.get(url).json()

    return responses

def init_weather(city_id: int, forecast: dict) -> dict:
    """Create weather dict for adding as row in df ."""
    timestamp = datetime.fromtimestamp(forecast.get('dt'))
    weather = {}
    weather['city_id'] = city_id
    weather['timestamp'] = timestamp

    return weather

def clean_responses(responses: dict) -> list:
    """Format response towards df row."""
    weather_list = []
    
    for city_id, response in responses.items():
        weather_content = response.get('list')
        
        for forecast in weather_content:
            weather = init_weather(city_id, forecast)
            
            for key, value in forecast.get('main').items():
                if key != 'temp_kf':
                    weather[key] = value
    
            for key, value in forecast.get('weather')[0].items():
                if key not in ['id', 'icon']:
                    weather['weather_' + key] = value
    
            for key, value in forecast.get('wind').items():
                weather['wind_' + key] = value

            weather['clouds'] = forecast.get('clouds').get('all')
            weather['visibility'] = forecast.get('visibility')
            weather['rain_prob'] = forecast.get('pop')
    
            weather_list.append(weather)

    return weather_list

def format_df_weather(df_weather: pd.DataFrame) -> pd.DataFrame:
    """Format df for sql preparation."""
    df_weather['humidity'] = df_weather['humidity'].astype(float)

    df_weather['rain_prob'] *= 100

    df_weather.loc[:, 'weather_main'] = df_weather['weather_main'].str.lower()

    df_weather = df_weather.rename(columns={
        'temp' : 'temperature',
        'timestamp' : 'forecast_time',
        'weather_description' : 'outlook'
    })

    return df_weather

def select_rel_cols(df: pd.DataFrame, rel_cols: list) -> pd.DataFrame:
    """Selecting relevant columns from df."""
    return df.loc[:, rel_cols]

def load_weather_info_to_sql(
    db_config: dict,
    api_config: dict,
    rel_cols=None
) -> pd.DataFrame:
    """
    Loads and formats weather forecast data for all cities and writes it to a SQL table.

    Args:
        db_config (dict): Database access parameters, including table and column names.
        api_config (dict): API credentials for OpenWeather.
        rel_cols (list, optional): List of relevant weather columns to retain.

    Returns:
        pd.DataFrame: Cleaned and structured weather data.
    """

    # Set default relevant columns if none provided
    if rel_cols is None:
        rel_cols = [
            "city_id",
            "forecast_time",
            "temperature",
            "feels_like",
            "humidity",
            "outlook",
            "wind_speed",
            "wind_gust",
            "visibility",
            "rain_prob"
        ]

    # --- Build SQL connection string
    connection_string = create_connection_string(
        schema=db_config.get("schema", "gans"),
        host=db_config.get("host", "127.0.0.1"),
        user=db_config.get("user", "root"),
        password=db_config.get("password"),
        port=db_config.get("port", 3306)
    )

    # --- Query city ID and coordinates from the database
    city_data = pd.read_sql(
        f"SELECT city_id, city_latitude, city_longitude FROM {db_config.get('sql_geo_table', 'geodata')}",
        con=connection_string
    ).dropna().values.tolist()

    # --- Fetch weather forecasts and process the data
    responses = get_weather_responses(city_data, api_key=api_config.get("weather")["key"])
    weather_list = clean_responses(responses)
    df_weather = pd.DataFrame(weather_list)
    df_weather = format_df_weather(df_weather)
    df_weather = select_rel_cols(df_weather, rel_cols)

    # --- Clear the SQL table before inserting new data
    clear_sql_table(
        connection_string=connection_string,
        sql_table=db_config.get("sql_weather_table", "weathers")
    )

    # --- Insert the cleaned weather data into SQL
    send_to_sql(
        df=df_weather,
        connection_string=connection_string,
        sql_table=db_config.get("sql_weather_table", "weathers")
    )

    return df_weather

### -------- FLIGHTS -------- ###
    
def get_timeranges() -> pd.DataFrame:
    """Returns two half-day time ranges for tomorrow in 'YYYY-MM-DDTHH:MM' format."""
    tomorrow = datetime.now() + timedelta(days=1)

    start1 = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0)
    end1 = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 11, 59)
    start2 = start1 + timedelta(hours=12)
    end2 = end1 + timedelta(hours=12)

    def fmt(dt):
        return dt.strftime("%Y-%m-%dT%H:%M")

    return ((fmt(start1), fmt(end1)), (fmt(start2), fmt(end2)))

def retrieve_flight_info(
    all_airport_codes: list,
    with_cancelled: bool,
    api_host: str,
    api_key: str,
    decoding: str,
    rel_objects: str,
    airport_code_type: str,
    delay_per_request: int
) -> pd.DataFrame:
    """Retrieves flight data from the API."""
    conn = http.client.HTTPSConnection(api_host)
    headers = {
        "x-rapidapi-key": api_key,
        'x-rapidapi-host': api_host
    }
    all_flights = []
    
    for airport_code in all_airport_codes:
        
        for time_start, time_end in get_timeranges():
            conn.request(
                "GET",
                f"/flights/airports/icao/{airport_code}/{time_start}/{time_end}?withLeg=false&direction=Arrival&withCancelled={with_cancelled}&withCodeshared=true&withCargo=false&withPrivate=true&withLocation=false",
                headers=headers
            )
            response = conn.getresponse()
    
            if response.status == 200:
                raw_data = response.read().decode(decoding)
                data = json.loads(raw_data)
                flights = pd.json_normalize(data.get(rel_objects, []))
                flights[airport_code_type] = airport_code
                all_flights.append(flights)
                
            else:
                print(f"API request failed for {airport_code} with status {response.status}.")
    
            conn.close()
            time.sleep(delay_per_request)

    return pd.concat(all_flights)

def format_flight_info(
    df: pd.DataFrame,
    col_name_revised_time: str,
    col_name_scheduled_time: str,
    relevant_columns: dict
) -> pd.DataFrame:
    """Formats the raw flight DataFrame from the API."""
    if col_name_revised_time and col_name_scheduled_time in df.columns:
        df[col_name_revised_time] = df[col_name_revised_time].fillna(df[col_name_scheduled_time])

    if col_name_revised_time in df.columns:
        df[col_name_revised_time] = pd.to_datetime(
            df[col_name_revised_time].str[:-6], errors='coerce'
        )

    df = df.loc[:, relevant_columns.keys()].rename(columns=relevant_columns)
    return df

def load_flight_info_to_sql(
    db_config: dict,
    api_config: dict,
    relevant_columns=None,
    time_columns=None,
    rel_objects="arrivals",
    with_cancelled=False
) -> pd.DataFrame:
    """
    High-level function to load, filter, format flight information and send to sql.

    Args:
        db_config (dict): DB access parameters
        api_config (dict): API host, key, etc.
        relevant_columns (dict): Relevant columns with rename mapping
        time_columns (dict): Name of scheduled and revised time columns
        rel_objects (str): API object name (e.g. "arrivals")
        with_cancelled (bool): Whether to include cancelled flights

    Returns:
        pd.DataFrame: Clean flight data
    """
    # --- Default column mapping ---
    if relevant_columns is None:
        relevant_columns = {
            'number' : 'flight_num',
            'movement.airport.icao': 'departure_icao',
            'icao' : 'arrival_icao',
            'movement.revisedTime.local' : 'arrival_time'
        }

    if time_columns is None:
        time_columns = {
            'scheduled' : 'movement.scheduledTime.local',
            'revised' : 'movement.revisedTime.local'
        }

    # --- Connection string ---
    connection_string = create_connection_string(
        schema=db_config.get("schema", "gans"),
        host=db_config.get("host", "127.0.0.1"),
        user=db_config.get("user", "root"),
        password=db_config.get("password"),
        port=db_config.get("port", 3306)
    )

    # --- Get known airports ---
    airport_codes = query_column_as_list_from_sql(
        connection_string=connection_string,
        sql_table=db_config.get("sql_airport_table", "airports"),
        column=db_config.get("sql_airport_code_column", "airport_icao")
    )

    # --- Call API ---
    df_flights = retrieve_flight_info(
        all_airport_codes=airport_codes,
        with_cancelled=with_cancelled,
        api_host=api_config.get("flights").get("host"),
        api_key=api_config.get("flights").get("key"),
        decoding=api_config.get("flights").get("decoding", "utf-8"),
        rel_objects=rel_objects,
        airport_code_type=api_config.get("flights").get("code_type", "icao"),
        delay_per_request=api_config.get("flights").get("delay", 2)
    )

    # --- Format result ---
    df_flights = format_flight_info(
        df=df_flights,
        col_name_revised_time=time_columns.get("revised"),
        col_name_scheduled_time=time_columns.get("scheduled"),
        relevant_columns=relevant_columns
    )

    # --- Clear SQL table ---
    clear_sql_table(
        connection_string=connection_string,
        sql_table=db_config.get("sql_flight_table", "flights")
    )

    # --- Send to SQL ---
    send_to_sql(
        df=df_flights,
        connection_string=connection_string,
        sql_table=db_config.get("sql_flight_table", "flights")
    )

    return df_flights 