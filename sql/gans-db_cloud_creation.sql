-- Drop the database if it already exists
DROP DATABASE IF EXISTS gans;

-- Create the database
CREATE DATABASE gans;

-- Use the database
USE gans;

-- Create the 'cities' table
CREATE TABLE cities (
    city_id INT AUTO_INCREMENT, -- Automatically generated ID for each city
    city_name VARCHAR(200) NOT NULL, -- Name of the city,
    city_country_code VARCHAR(2) NOT NULL, -- Country code of the city
    PRIMARY KEY (city_id) -- Primary key to uniquely identify each city
);

-- Create the 'populations' table
CREATE TABLE populations (
	city_id INT, -- ID of the city
    population INT, -- Population of the city
    timestamp_population DATE, -- Timestamp for last scraping the data from wikipedia
	PRIMARY KEY (city_id), -- Primary key to uniquely identify each city
    FOREIGN KEY (city_id) REFERENCES cities(city_id) -- Foreign key to connect each city to its population
);

-- Create the 'geodata' table
CREATE TABLE geodata (
	city_id INT, -- ID of the city
    city_latitude DECIMAL(9,6), -- Latitude of the city
    city_longitude DECIMAL(9,6), -- Longitude of the city
	PRIMARY KEY (city_id), -- Primary key to uniquely identify each city
    FOREIGN KEY (city_id) REFERENCES cities(city_id) -- Foreign key to connect each city to its geodata
);

-- Create the 'weathers' table
CREATE TABLE weathers (
	id INT AUTO_INCREMENT, -- Automatically generated ID for each forecast
    city_id INT, -- ID of the city
    forecast_time DATETIME, -- Timestamp of for forecast
    temperature DECIMAL(5,2), -- Forecast temperature in celcius
    feels_like DECIMAL(5, 2), -- Temperature felt in celsius
    humidity DECIMAL(5, 2), -- Rel humidity in percent
    outlook VARCHAR(200), -- Weather outlook in words
    wind_speed DECIMAL(5, 2), -- Wind speed in m/s
    wind_gust DECIMAL(5, 2), -- Wind gust speed in m/s
    visibility INT, -- Visibility in m
    rain_prob DECIMAL(5, 2), -- Rain probability in percent
	PRIMARY KEY (id), -- Primary keys to uniquely identify each city
    FOREIGN KEY (city_id) REFERENCES cities(city_id) -- Foreign key to connect each city to its geodata
);

-- Create the 'airports' table
CREATE TABLE airports (
	airport_icao VARCHAR(4), -- ICAO for airport
    airport_name VARCHAR(255), -- Name of airport
	PRIMARY KEY (airport_icao) -- Primary key to uniquely identify each airport
);

-- Create the 'cities_airports' table
CREATE TABLE cities_airports (
	city_id INT, -- ID for the city
    airport_icao VARCHAR(4), -- ICAO for airport
	PRIMARY KEY (city_id, airport_icao), -- Primary keys to uniquely identify each city-airport combination
    FOREIGN KEY (city_id) REFERENCES cities(city_id), -- Foreign key to connect each airport to its city
    FOREIGN KEY (airport_icao) REFERENCES airports(airport_icao) -- Foreign key to connect each aiport to its name
);

-- Create the 'flights' table
CREATE TABLE flights (
	flight_id INT AUTO_INCREMENT, -- Automatically generated ID for each flight
    flight_num VARCHAR(25), -- Official flight no.
    departure_icao VARCHAR(4), -- ICAO for departure airport
    arrival_icao VARCHAR(4), -- ICAO for arrival airport
    arrival_time DATETIME, -- Revised (local) arrival time
	PRIMARY KEY (flight_id), -- Primary keys to uniquely identify each flight
    FOREIGN KEY (arrival_icao) REFERENCES airports(airport_icao) -- Foreign key to connect each flight to its departure airport
);
	