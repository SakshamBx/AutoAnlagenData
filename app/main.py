from flask import Flask, jsonify , request
import requests
import json
import os
from datetime import datetime
import schedule
import time
import logging
from logging.handlers import RotatingFileHandler
import threading


# State codes in url-
# W - Wien
# NO - Niederösterreich
# B - Burgenland
# S - Salzburg
# K - Kärnten
# ST - Steiermark
# OO - Oberösterreich
# T - Tirol
# V - Vorarlberg


# sample request body for post request
# Anlagename=&Anlagestrasse=&AnlagePlz=&AnlageOrt=&Anlagentyp=1&Bundesland={State code here}&Energietraeger=9
# Anlagentyp = 1 - is for strom
# Energietraeger = 9 - is for sonnenenergie
# Bundesland = {State code here from the list above} - is for state code


app = Flask(__name__)


# logging
app.logger.setLevel(logging.INFO)
log_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=1)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(log_handler)

#methods
def write_source_to_json_file(data, filename):
    directory = "../app/data/source"
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)

    timestamp = datetime.now().isoformat()
    datalist = data["Data"]
    data_count = len(datalist)

    modified_data = []
    for item in datalist:
      modified_item = {
        "ID": item["ID"],
        "AnlPlz": item["AnlPlz"],
        "AnlOrt": item["AnlOrt"],
        "Engpassleistung": item["Engpassleistung"],
        "Eingespeister Strom 2023" : item["Jahressumme_Minus_1"],
        "Eingespeister Strom 2022" : item["Jahressumme_Minus_2"],
        "Eingespeister Strom 2021" : item["Jahressumme_Minus_3"],
        "Eingespeister Strom 2020" : item["Jahressumme_Minus_4"],
        "Eingespeister Strom 2019" : item["Jahressumme_Minus_5"],
        "Eingespeister Strom 2018" : item["Jahressumme_Minus_6"]
      }
      modified_data.append(modified_item)

    data_dict = {
      "TimeFetched" : timestamp,
      "Bundesland" : filename.split(".")[0],
      "DataCount" : data_count,
      "Data" : modified_data
    }

    with open(filepath, "w") as f:
        json.dump(data_dict, f)
        # print("Successfully saved data to: ", f.name)
        app.logger.info(f"Successfully saved data to: {f.name}")


def send_request(bundesland, url, headers):
    try:
      payload = f"Anlagename=&Anlagestrasse=&AnlagePlz=&AnlageOrt=&Anlagentyp=1&Bundesland={bundesland}&Energietraeger=9"
      # print("Fetching data for: ", bundesland)
      app.logger.info(f"Fetching data for: {bundesland}")
      response = requests.post(url, headers=headers, data=payload)
      # print(payload)
      if response.status_code == 200:
          # print(f"Successfully fetched data for {bundesland}")
          app.logger.info(f"Successfully fetched data for {bundesland}")
          
          # parse response data to json
          response_data = response.json()

          # save response data to json file
          write_source_to_json_file(response_data, f"{bundesland}_source.json")
      # print("------------------------------------------")
      app.logger.info("------------------------------------------")
    except Exception as e:
      # print(f"Error while fetching/saving data for {bundesland}: ", e)
      app.logger.info(f"Error while fetching/saving data for {bundesland}: {e}")


def getdata():
  url = "https://anlagenregister.at//Home/SearchAnlagenregisterUebersicht"
  bundesland_values = ['W', 'NO', 'B', 'S', 'K', 'ST', 'OO', 'T', 'V']
  headers = {
      'authority': 'anlagenregister.at',
      '_appcontext': '{}',
      'accept': 'application/json, text/javascript, */*; q=0.01',
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
      'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'cookie': '_currentLanguage=de',
      'origin': 'https://anlagenregister.at',
      'referer': 'https://anlagenregister.at/',
      'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
      'sec-fetch-dest': 'empty',
      'sec-fetch-mode': 'cors',
      'sec-fetch-site': 'same-origin',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'x-requested-with': 'XMLHttpRequest'
    }

  # parallelize requests
  threads = []
  for bundesland in bundesland_values:
    thread = threading.Thread(target=send_request, args=(bundesland, url, headers))
    thread.start()
    threads.append(thread)

  for thread in threads:
    thread.join()

  

# endpoints
@app.route('/getanlagendata', methods=['GET'])
def getanlagendata():
  getdata()
  return "Successfully fetched data from anlagenregister.at"


@app.route('/')
def hello_world():
    return 'Hello, World!'


# daily schedule to fetch data from anlagenregister.at
schedule.every().day.at("00:00").do(getdata)


def run_schedule():
  while True:
    schedule.run_pending()
    time.sleep(1)


# main
if __name__ == '__main__':
  
  threading.Thread(target=run_schedule).start()

  app.run(debug=True)

