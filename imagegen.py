from openai import OpenAI
import requests
import datetime
import re
import replicate
from PIL import Image
import os
import base64


def make_filename_friendly(input_string):
    # Remove non-alphanumeric characters and replace spaces with underscores
    friendly_string = re.sub(r'\W+', '_', input_string.strip())

    # Get the current date
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 

    # Append the date to the friendly string
    filename = f"{friendly_string}_{current_date}"

    return filename

def resize_resolution(width, height, min_size=256, max_size=1440):
    # Find the largest dimension to base the scaling on
    max_dim = max(width, height)
    min_dim = min(width, height)

    # Calculate the scaling factor to stay within the min and max bounds
    scale_factor = min(max_size / max_dim, max(min_size / min_dim, 1))

    # Apply the scaling factor to width and height
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    return new_width, new_height

def resize_png(input_path, output_path, new_width, new_height):
    # Open the image file
    with Image.open(input_path) as img:
        # Resize to custom dimensions
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        # Save the resized image
        img_resized.save(output_path)
        print(f"Image resized to custom size: {new_width}x{new_height}")

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


# Example usage
block_of_text_user ="Apple tree"
input_width, input_height = 800, 480


new_width, new_height = resize_resolution(input_width, input_height)
print(f"New resolution: {new_width}x{new_height}")

client = OpenAI()







filename_raw = make_filename_friendly(block_of_text_user) + "_r1.png"
filename_final = make_filename_friendly(block_of_text_user) + "_f1.png"

block_of_text_system1 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system2 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing pensils.
"""


messages=[
    {"role": "system", "content": block_of_text_system1},
    {"role": "user", "content": block_of_text_user}
  ]


completion = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=messages
)


image_text = completion.choices[0].message.content
print(image_text)



output = replicate.run(
    "black-forest-labs/flux-1.1-pro",
    input={
        "width": new_width,
        "height": new_height,
        "prompt": image_text,
        "aspect_ratio": "custom",
        "output_format": "png",
        "output_quality": 80,
        "safety_tolerance": 5,
        "prompt_upsampling": True
    },
     timeout=120
)
print(output.url)

if isinstance(output.url, str) and output.url.startswith('data:image/png;base64'):
    save_base64_as_png(output.url, filename_raw)
else:

    # Download and save the image if the output is a URL
    if isinstance(output.url, str) and output.url.startswith('http'):
        response = requests.get(output)
        if response.status_code == 200:
            with open(filename_raw, 'wb') as file:
                file.write(response.content)
            print(f"Image saved as {filename_raw}")
        else:
            print("Failed to download the image")

resize_png(filename_raw, filename_final, input_width, input_height)

# delete the raw image

os.remove(filename_raw)
print(f"Deleted the raw image {filename_raw}")