from openai import OpenAI
import requests
import datetime
import re
from datetime import datetime
import base64


def format_weather_data(data):
    location = data['location']
    current = data['current']
    condition = current['condition']
    
    readable_text = (
        f"Weather Information for {location['name']}\n"  #, {location['region']}, {location['country']}
        f"Local Time: {location['localtime']}\n\n"
        f"Current Conditions:\n"
        f"  - Temperature: {current['temp_c']}°C \n"
        f"  - Condition: {condition['text']}\n"
      #  f"  - Wind: {current['wind_mph']} mph ({current['wind_kph']} kph) from {current['wind_dir']} (Degree: {current['wind_degree']})\n"
       # f"  - Pressure: {current['pressure_mb']} mb ({current['pressure_in']} in)\n"
    #    f"  - Precipitation: {current['precip_mm']} mm \n"
     #   f"  - Humidity: {current['humidity']}%\n"
        f"  - Cloud Cover: {current['cloud']}%\n"
    #    f"  - Feels Like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)\n"
      #  f"  - Dew Point: {current['dewpoint_c']}°C ({current['dewpoint_f']}°F)\n"
       # f"  - Visibility: {current['vis_km']} km ({current['vis_miles']} miles)\n"
       # f"  - UV Index: {current['uv']}\n"
       # f"  - Gusts: {current['gust_mph']} mph ({current['gust_kph']} kph)\n"
    )
    
    return readable_text

def make_filename_friendly(input_string):
    # Remove non-alphanumeric characters and replace spaces with underscores
    friendly_string = re.sub(r'\W+', '_', input_string.strip())

    # Get the current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # Append the date to the friendly string
    filename = f"{friendly_string}_{current_date}"

    return filename

def save_base64_as_png(data_url, file_name="output.png"):
    # Check if the string starts with the correct data URL prefix
    if data_url.startswith("data:image/png;base64,"):
        # Remove the prefix from the base64 string
        base64_data = data_url.replace("data:image/png;base64,", "")
        
        # Decode the base64 string
        image_data = base64.b64decode(base64_data)
        
        # Write the binary data to a .png file
        with open(file_name, "wb") as png_file:
            png_file.write(image_data)
        print(f"PNG file saved as {file_name}")
    else:
        print("The provided string does not contain a base64-encoded PNG image.")


client = OpenAI()

responsew1 = requests.get("http://api.weatherapi.com/v1/current.json?key=13d9ff9d65f74b2db9f115700241907&q=Randburg")

wdata = responsew1.json()
temperature_text = str(wdata['current']['temp_c']) + "°C"
block_of_text_user = format_weather_data(wdata) 
print(block_of_text_user)
# Get current date and time
now = datetime.now()

# Format as YYYYMMDD_HHMMSS
compact_datetime = now.strftime("%Y%m%d_%H%M%S")
filename = compact_datetime + "_w7_r.png"


block_of_text_system1 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system2 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing pensils.
"""

block_of_text_system3 = """
You are good in image text generation for a given weather and describe the image. Make a closup and some pop. Make it display the temperature in big  text. Make sure the background match the time of day, day or night.  The color palette is limited to black, white , red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution.No explanation just the Description.
"""

block_of_text_system4 = """
You are good in image text generation for a given weather and describe the image. Make a closup and some pop. Make it display the temperature in big text. With smaller text the weather forcast in max three words.  Make sure the background match the time of day, day or night.  The color palette is limited to black, white , red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""
messages=[
    {"role": "system", "content": block_of_text_system3},
    {"role": "user", "content": block_of_text_user}
  ]

#model="gpt-4-1106-preview",
completion = client.chat.completions.create(
  model="gpt-5-mini",
  messages=messages
 
  
)
#print(completion.choices[0].message)

image_text = completion.choices[0].message.content
image_text = image_text.replace('**"', '"').replace("**", '"')
print(image_text)

