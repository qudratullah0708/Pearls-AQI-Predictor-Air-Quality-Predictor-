import requests
import pandas as pd
import os


TOKEN = "2e97ca37e132ceb2dc9656d1c55460e385a4456c"
CITY = "islamabad"
URL = f"http://api.waqi.info/feed/{CITY}/?token={TOKEN}"




def fetch_data():
    # Calls AQICN API, returns JSON
    response = requests.get(URL)
    print("calling api")
    if response.status_code == 200:
        data = response.json()
        print("api called successfully")
        return data
    else:
        print("Error:", response.status_code, response.text)
        print("api call failed")
        return None



def parse_features(data):
    print("parsing features")
    features = {}
    features["timestamp"] = data["data"]["time"]["s"]
    features["city"] = data["data"]["city"]["name"]
    features["aqi"] = data["data"]["aqi"]
    features["dominant_pollutant"] = data["data"]["dominentpol"]
    features["pm25"] = data["data"]["iaqi"]["pm25"]["v"]
    #features["pm10"] = data["data"]["iaqi"]["pm10"]["v"]
    features["latitude"] = data["data"]["city"]["geo"][0]
    features["longitude"] = data["data"]["city"]["geo"][1]
    features["dew"] = data["data"]["iaqi"]["dew"]["v"]
    features["humidity"] = data["data"]["iaqi"]["h"]["v"]
    features["pressure"] = data["data"]["iaqi"]["p"]["v"]
    features["temp"] = data["data"]["iaqi"]["t"]["v"]
    features["wind_speed"] = data["data"]["iaqi"]["w"]["v"]
    
    df = pd.DataFrame([features])  # convert dict to 1-row DataFrame
    print("features parsed successfully")
    return df



def engineer_features(df):
    print("engineering features")
    # Add time-based + derived columns
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["year"] = df["timestamp"].dt.year
    aqi_change = df["aqi"].diff()
    aqi_roll3 = df["aqi"].rolling(window=3).mean()
    df["aqi_change"] = aqi_change
    df["aqi_roll3"] = aqi_roll3
    print("features engineered successfully")
    return df
#

def save_to_store(new_df):
    print("saving to store")
    path = "aqi_data.csv"
    if os.path.exists(path):
        old_df = pd.read_csv(path)
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    combined_df = engineer_features(combined_df)
    if not combined_df["timestamp"].duplicated().any():
        combined_df.to_csv(path, index=False)
    print("data saved successfully")


def main():
    data = fetch_data()
    df = parse_features(data)
    df = engineer_features(df)
    save_to_store(df)



if __name__ == "__main__":
    main()

