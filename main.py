import requests
import os
from headers import *
from bs4 import BeautifulSoup
import json
import pandas as pd
import uuid
from geopy.geocoders import Nominatim
import openai
openai.api_key = ""

################################################################################################################

def get_coordinates(location):
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if location_data:
        latitude = location_data.latitude
        longitude = location_data.longitude
        return latitude, longitude
    else:
        print(f"Coordinates not found for {location}")
        return '', ''

################################################################################################################

def get_data_from_openai(text):
    prompt = f'return project "original_id", "region_name", "region_code"(code of region in 2-4 letters), "title", "description", "status", "stages", "date_published", "procurementMethod", "budget", "currency", "buyer", "sector", "subsector" in single line string json format from this data : {text} . If any data is not present then return empty string'

    refined_answer = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=200
    )
    refined_answer = refined_answer['choices'][0]['text']
    refined_answer = json.loads(refined_answer)
    return refined_answer

################################################################################################################

def add_data_to_csv(data_list):
    if os.path.exists('output_data.csv'):
        existing_df = pd.read_csv('output_data.csv')
        duplicates = existing_df[existing_df['original_id'].isin(data['original_id'] for data in data_list)]
        if not duplicates.empty:
            print(f"Duplicates found for original_ids: {duplicates['original_id'].tolist()}")
            print("Not appending duplicate data.")
            return
        updated_df = existing_df.append(data_list, ignore_index=True)
    else:
        updated_df = pd.DataFrame(data_list)
    updated_df.to_csv('output_data.csv', index=False)
    print(f"Data appended to '{'output_data.csv'}'")

################################################################################################################

def get_rpcity_data(url):
    response = requests.get(url=url,headers=headers_rpcity)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        projects = soup.select('div.accordion')
        data_list = []
        for project in projects:
            data = get_data_from_openai(project.text)
            data['aug_id'] = str(uuid.uuid4())
            data['country_name'] = 'california'
            data['country_code'] = 'ca'
            latitude, longitude = get_coordinates(data['region_name'])
            data['map_coordinates'] = {
                "type": "Point",
                "coordinates": [longitude, latitude]
            }
            data_list.append(data)
        add_data_to_csv(data_list)
            
################################################################################################################
            
def get_ppmoe_data(url):
    response = requests.get(url=url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        projects = soup.select('div.project-container')
        data_list = []
        for project in projects:
            data = get_data_from_openai(project.text)
            data['aug_id'] = str(uuid.uuid4())
            data['country_name'] = 'california'
            data['country_code'] = 'ca'
            latitude, longitude = get_coordinates(data['region_name'])
            data['map_coordinates'] = {
                "type": "Point",
                "coordinates": [longitude, latitude]
            }
            data_list.append(data)
        add_data_to_csv(data_list)

################################################################################################################

urls = [
    'https://www.rpcity.org/city_hall/departments/development_services/engineering/projects_in_progress', 
    'https://ppmoe.dot.ca.gov/des/oe/weekly-ads/all-adv-projects.php']

# Similarly we can add more urls and add subsequent scroing function for more urls

for url in urls:
    if 'rpcity' in url:
        get_rpcity_data(url)
    if 'ppmoe' in url:
        get_ppmoe_data(url)