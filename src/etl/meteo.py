import requests
import os
from datetime import datetime, timedelta
import requests_cache
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry


meteo_url = "https://api.open-meteo.com/v1/forecast"



# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below

def extraction_meteo_data(latitude,
                          longitude, 
                          past_days, 
                          ):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "surface_pressure", "apparent_temperature", "wind_speed_80m", "wind_direction_80m", "temperature_80m", "soil_temperature_18cm", "soil_moisture_3_to_9cm"],
        "timezone": "auto",
        "past_days": past_days,
        # "forecast_days": forecast_days,
    }
    responses = openmeteo.weather_api(meteo_url, params = params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

        # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_surface_pressure = hourly.Variables(3).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_speed_80m = hourly.Variables(5).ValuesAsNumpy()
    hourly_wind_direction_80m = hourly.Variables(6).ValuesAsNumpy()
    hourly_temperature_80m = hourly.Variables(7).ValuesAsNumpy()
    hourly_soil_temperature_18cm = hourly.Variables(8).ValuesAsNumpy()
    hourly_soil_moisture_3_to_9cm = hourly.Variables(9).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
            end =  pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["surface_pressure"] = hourly_surface_pressure
    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
    hourly_data["wind_direction_80m"] = hourly_wind_direction_80m
    hourly_data["temperature_80m"] = hourly_temperature_80m
    hourly_data["soil_temperature_18cm"] = hourly_soil_temperature_18cm
    hourly_data["soil_moisture_3_to_9cm"] = hourly_soil_moisture_3_to_9cm

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # saved the dataframe as a csv file for later use
    os.makedirs("data/raw", exist_ok = True)
    hourly_dataframe.to_csv("data/raw/hourly_meteo_data.csv", index = False)
    return hourly_dataframe
    

if __name__ == "__main__":      
    latitude = 6.37
    longitude = 2.42
    past_days = 92
    # forecast_days = 24
    meteo_data = extraction_meteo_data(latitude, longitude, past_days,)
    print(meteo_data.head())
