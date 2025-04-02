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
    friendly_string = re.sub(r'\W+', ' ', input_string.strip())
    
    # Limit to the first 5 words
    words = friendly_string.split()[:5]
    truncated_string = '_'.join(words)
    
    # Ensure the string is no more than 50 characters
    if len(truncated_string) > 50:
        truncated_string = truncated_string[:50].rstrip('_')

    # Get the current date
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Append the date to the friendly string
    filename = f"{truncated_string}_{current_date}"

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


def find_best_match(input_size):
    # Allowed resolutions
    allowed_resolutions = [
        "1024x1024", "1365x1024", "1024x1365", "1536x1024", "1024x1536",
        "1820x1024", "1024x1820", "1024x2048", "2048x1024", "1434x1024",
        "1024x1434", "1024x1280", "1280x1024", "1024x1707", "1707x1024"
    ]
    
    # Parse the input resolution
    try:
        input_width, input_height = map(int, input_size.split('x'))
    except ValueError:
        return "Invalid input size format. Use 'WIDTHxHEIGHT'."

    # Calculate aspect ratio for the input size
    input_aspect_ratio = input_width / input_height
    
    # Helper function to calculate aspect ratio
    def get_aspect_ratio(resolution):
        width, height = map(int, resolution.split('x'))
        return width / height

    # Find the best match based on the closest aspect ratio
    best_match = None
    smallest_difference = float('inf')

    for resolution in allowed_resolutions:
        allowed_aspect_ratio = get_aspect_ratio(resolution)
        difference = abs(input_aspect_ratio - allowed_aspect_ratio)
        
        if difference < smallest_difference:
            smallest_difference = difference
            best_match = resolution

    return best_match

def closest_aspect_ratio(width, height):
    # List of aspect ratios with name and float value
    aspect_ratios = {
        "1:1": 1.0,
        "16:9": 16/9,
        "21:9": 21/9,
        "3:2": 3/2,
        "2:3": 2/3,
        "4:5": 4/5,
        "5:4": 5/4,
        "3:4": 3/4,
        "4:3": 4/3,
        "9:16": 9/16,
        "9:21": 9/21
    }

    # Compute target aspect ratio
    target_ratio = width / height

    # Find the closest ratio by absolute difference
    closest = min(aspect_ratios.items(), key=lambda ar: abs(ar[1] - target_ratio))

    return {
        "input_resolution": f"{width}x{height}",
        "target_ratio": round(target_ratio, 4),
        "closest_match": closest[0],
        "matched_ratio_value": round(closest[1], 4)
    }



# Example usage
block_of_text_user ="a puppy in a busket"
input_width, input_height = 264, 176
#input_width, input_height = 296, 128
#input_width, input_height = 360, 184
#input_width, input_height = 1200, 1600
#input_width, input_height = 960, 640

new_width, new_height = resize_resolution(input_width, input_height)
print(f"New resolution: {new_width}x{new_height}")

result_ratio = closest_aspect_ratio(input_width, input_height)
print(result_ratio.get("closest_match"))

client = OpenAI()







filename_raw = make_filename_friendly(block_of_text_user) + "_r1"
filename_final = make_filename_friendly(block_of_text_user) + "_f1.png"

block_of_text_system1 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system2 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing pensils.
"""

block_of_text_system3 = """
You are good in image text generation for a given input and describe the image. Make a silhouette of the subject , in the style of cyclorama, light yellow and red, middle of the sun, tokina opera 50mm f/1.4 ff, surrealistic poses, light sculptures, acrobatic self-portraits, emotive gestures
"""

block_of_text_system4 = """
You are good in image text generation for a given input and describe the image.Make a closup , rendered in Pulp Fiction Halftone Noir style, where dramatic dot patterns create a gritty, vintage comic book aesthetic. Utilize contrasting red and yellow halftone dots of varying sizes to build tension and mystery 
"""

block_of_text_system5 = """
You are good in image text generation for a given input and describe the image. Make sure the prompt does not exeeds 500 characters.  Make a closup , rendered in a Retro Sci-Fi  featuring the subject, with dramatic poses and outlandish scenarios typical of 1930s-1950s science fiction. Utilize bold red and yellow for a striking, vintage look
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

image_size = "" + str(input_width) + "x" + str(input_height)
print(image_size)

best_match = find_best_match(image_size)
print(f"The best match for {image_size} is {best_match}.")

output = replicate.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": image_text,
        "go_fast": True,
        "megapixels": "1",
        "num_outputs": 1,
        "aspect_ratio": result_ratio.get("closest_match"),
        "output_format": "png",
        "output_quality": 80,
        "num_inference_steps": 2
    }
)
print(output)


# output = replicate.run(
#     "nvidia/sana-sprint-1.6b:c91d3bf9efbb9f135fc7f291436938cf3f8d29bd558a54b1cbe6cf112b9bf00d",
#     input={
#         "seed": -1,
#         "width": new_width,
#         "height": new_height,
#         "prompt": image_text,
#         "guidance_scale": 4.5,
#         "inference_steps": 2
#     }
# )
# print(output)
#"1365x1024",
# output = replicate.run(
#     "recraft-ai/recraft-v3",
#     input={
#         "size": best_match,
#         "style": "digital_illustration",
#         "prompt": image_text
#     }
# )
# print(output)


# output = replicate.run(
#     "black-forest-labs/flux-1.1-pro",
#     input={
#         "width": new_width,
#         "height": new_height,
#         "prompt": image_text,
#         "aspect_ratio": "custom",
#         "output_format": "png",
#         "output_quality": 80,
#         "safety_tolerance": 5,
#         "prompt_upsampling": True
#     },
#      timeout=240
# )

imageurl = output[0].url
print(imageurl)

if isinstance(imageurl, str) and imageurl.startswith('data:image/png;base64'):
    save_base64_as_png(imageurl, filename_raw)
else:

    # Download and save the image if the output is a URL
    if isinstance(imageurl, str) and imageurl.startswith('http'):
        # get output file extension
        extension_raw = imageurl.split('.')[-1]
        filename_raw = filename_raw + "." + extension_raw
        response = requests.get(imageurl)
        if response.status_code == 200:
            with open(filename_raw, 'wb') as file:
                file.write(response.content)
            print(f"Image saved as {filename_raw}")
        else:
            print("Failed to download the image")

resize_png(filename_raw, filename_final, input_width, input_height)

# delete the raw image

#os.remove(filename_raw)
#print(f"Deleted the raw image {filename_raw}")