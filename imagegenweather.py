from openai import OpenAI
import requests
import datetime
import re
from datetime import datetime
import replicate
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

output = replicate.run(
                "ideogram-ai/ideogram-v2a-turbo",
                input={
                    "prompt": image_text,
                    "resolution": "None",
                    "style_type": "Design",
                    "aspect_ratio": "3:2",
                    "magic_prompt_option": "Auto"
                }
            )

#1248 × 832 (Landscape)
# output = replicate.run(
#             "prunaai/hidream-l1-fast:17c237d753218fed0ed477cb553902b6b75735f48c128537ab829096ef3d3645",
#             input={
#                 "seed": -1,
#                 "prompt": image_text,
#                 "model_type": "fast",
#                 "resolution":"1248 × 832 (Landscape)",
#                 "speed_mode": "Lightly Juiced 🍊 (more consistent)",
#                 "output_format": "png",
#                 "output_quality": 80
#             },
#             timeout=600
#         )
# output = replicate.run(
#     "black-forest-labs/flux-1.1-pro",
#     input={
#         "width": 960,
#         "height": 640,
#         "prompt": image_text,
#         "aspect_ratio": "custom",
#         "output_format": "png",
#         "output_quality": 80,
#         "safety_tolerance": 1,
#         "prompt_upsampling": True
#     },
#     timeout=240
# )
print(output.url)

if isinstance(output.url, str) and output.url.startswith('data:image/png;base64'):
    save_base64_as_png(output.url, filename)
else:

  # Download and save the image if the output is a URL
  if isinstance(output.url, str) and output.url.startswith('http'):
      response = requests.get(output)
      if response.status_code == 200:
          with open(filename, 'wb') as file:
              file.write(response.content)
          print("Image saved as 'output_image.png'")
      else:
          print("Failed to download the image")

#imagetext ="""
#Since I can't generate images, let's create a textual description of the image instead.\n\nPicture a simple, yet striking image that focuses on a horse. This is a close-up, so the horse's features are front and center, occupying most of the frame. Its mane is a deep, rich black, billowing softly as if caught in a gentle breeze. The horse's coat is a glossy white, almost shining, with the light hitting it in a way that it seems to gleam. Its eyes are a captivating, vibrant red, full of life and cheer.\n\nThe background is pure white, to emphasize the contrast and to keep the image minimalistic. Around the horse's head, there's a subtle red flare, which gives the image a bit of an ethereal glow. The flare is not overpowering but provides a warm, cheerful aura that complements the horse's own cheerfulness.\n\nDespite the limited color palette, the image feels full of life and joy, playing with the stark contrasts to create an engaging and simplistic visual that captivates the viewer
#"""
#size="1792x1024",
#standard
cnt1 = 0
while True:

    response = client.images.generate(
      model="gpt-image-1",
      prompt=image_text,
     
    )
#  size="1792x1024",
#       quality="hd",
#       n=1,
    image_url1 = response.data[0].url

    response5 = requests.get(image_url1)
    file1 = open("w"+ str(cnt1) + filename, "wb")
    file1.write(response5.content)
    file1.close()

    response1a = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {
          "role": "user",
          "content": [
            {"type": "text", "text": "Is this text of temperature "+temperature_text+" in the image? Only replay with yes or no."},
            {
              "type": "image_url",
              "image_url": {
                "url": image_url1,
              },
            },
          ],
        }
      ],
      max_tokens=300,
    )

    print(response1a.choices[0])

    reply1 = response1a.choices[0].message.content

    

    if response1a.choices[0].message.content == "Yes.":
        break
    
    cnt1 += 1
    if cnt1 > 2:
        break  

print("Image saved to", filename)