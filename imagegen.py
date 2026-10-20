from openai import OpenAI
import requests
import datetime
import re
import replicate
from PIL import Image
import os
import base64
import time

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

def resize_and_crop(input_path, output_path, new_width, new_height):
    # Open the image file
    with Image.open(input_path) as img:
        orig_width, orig_height = img.size
        target_ratio = new_width / new_height
        orig_ratio = orig_width / orig_height

        # Check if cropping is necessary
        if orig_ratio > target_ratio:
            # Original image is wider than target ratio:
            # Calculate new width based on the original height
            new_orig_width = int(target_ratio * orig_height)
            left = (orig_width - new_orig_width) // 2
            right = left + new_orig_width
            top = 0
            bottom = orig_height
            img_cropped = img.crop((left, top, right, bottom))
        elif orig_ratio < target_ratio:
            # Original image is taller than target ratio:
            # Calculate new height based on the original width
            new_orig_height = int(orig_width / target_ratio)
            top = (orig_height - new_orig_height) // 2
            bottom = top + new_orig_height
            left = 0
            right = orig_width
            img_cropped = img.crop((left, top, right, bottom))
        else:
            # Aspect ratios are the same, no crop needed
            img_cropped = img

        # Resize the (possibly cropped) image to the desired dimensions
        img_resized = img_cropped.resize((new_width, new_height), Image.LANCZOS)
        img_resized.save(output_path)
        print(f"Image resized and cropped to {new_width}x{new_height}")

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


def extract_resolutions(resolutions):
    """
    Extracts width and height from a list of resolution strings.
    
    Parameters:
        resolutions (list): A list of resolution strings, e.g., "1024 × 1024 (Square)".
    
    Returns:
        list: A list of tuples where each tuple contains (width, height) as integers.
    """
    extracted = []
    for res in resolutions:
        # Use regex to find two groups of digits separated by the multiplication sign (×)
        match = re.search(r"(\d+)\s*×\s*(\d+)", res)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            extracted.append((width, height,res))
        else:
            print(f"Could not extract resolution from: {res}")
    return extracted

def find_closest_aspect_ratio(target_width, target_height, resolution_list):
    """
    Finds the resolution from the list that has the closest aspect ratio to the target.
    
    Parameters:
        target_width (int): The target width.
        target_height (int): The target height.
        resolution_list (list): A list of tuples, each tuple is (width, height).
        
    Returns:
        tuple: The resolution tuple with the closest aspect ratio.
    """
    target_ratio = target_width / target_height
    closest = None
    min_diff = float('inf')
    
    for width, height,orig_str  in resolution_list:
        current_ratio = width / height
        diff = abs(target_ratio - current_ratio)
        if diff < min_diff:
            min_diff = diff
            closest = (width, height, orig_str)
    
    return closest

# List of allowed resolutions
allowed_resolutions2 = [
    "1024 × 1024 (Square)",
    "768 × 1360 (Portrait)",
    "1360 × 768 (Landscape)",
    "880 × 1168 (Portrait)",
    "1168 × 880 (Landscape)",
    "1248 × 832 (Landscape)",
    "832 × 1248 (Portrait)"
]


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
block_of_text_user ="3 May 2025"
input_width, input_height = 200, 200
# input_width, input_height = 264, 176
#input_width, input_height = 296, 128
#input_width, input_height = 360, 184
#input_width, input_height = 300, 400
# input_width, input_height = 512, 368
#input_width, input_height = 800, 272
#input_width, input_height = 800, 480
#input_width, input_height = 1200, 1600
#input_width, input_height = 960, 640

resolutions = extract_resolutions(allowed_resolutions2)
closest_resolution = find_closest_aspect_ratio(input_width,input_height , resolutions)


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


block_of_text_system_time1 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system_time2 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing pensils.
"""

block_of_text_system_time3 = """
You are good in image text generation for a given time of day and describe the image. Make a closup and some pop. Make it display the time in big digital text. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system_date1 = """
You are good in image text generation for a given date of the year in the southern hemisphere and describe the image. Make sure the date format is day, month year. Make a closup and some pop. Make it display the date in big text. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. Just give me the raw prompt, no explanation.
"""

block_of_text_system_date2 = """
You are good in image text generation for a given date of the year and make the theme "Car (Simple Side Profile)". Make sure the date format is day, month year. Make a closup and some pop.No people just objects. Make it display the date in big text. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution.Just give me the raw prompt, no explanation.
"""

messages=[
    {"role": "system", "content": block_of_text_system_date2},
    {"role": "user", "content": block_of_text_user}
  ]


completion = client.chat.completions.create(
  model="gpt-4.1-mini",
  messages=messages
)



image_text = completion.choices[0].message.content
print(image_text)

image_size = "" + str(input_width) + "x" + str(input_height)
print(image_size)

best_match = find_best_match(image_size)
print(f"The best match for {image_size} is {best_match}.")



retrycount = 0
while retrycount < 3:
    retrycount += 1



   
    try:
        if retrycount > 1:
            output = replicate.run(
                "ideogram-ai/ideogram-v2a-turbo",
                input={
                    "prompt": image_text,
                    "resolution": "None",
                    "style_type": "Design",
                    "aspect_ratio": result_ratio.get("closest_match"),
                    "magic_prompt_option": "Auto"
                }
            )
        else:
            output = replicate.run(
                "prunaai/hidream-l1-fast:17c237d753218fed0ed477cb553902b6b75735f48c128537ab829096ef3d3645",
                input={
                    "seed": -1,
                    "prompt": image_text,
                    "model_type": "fast",
                    "resolution": closest_resolution[2],
                    "speed_mode": "Lightly Juiced 🍊 (more consistent)",
                    "output_format": "png",
                    "output_quality": 80
                },
                timeout=600
            )

        imageurl = output.url
        print(imageurl)
    except Exception as e:
        import traceback
        print("An error occurred during the replicate.run call:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        # print("Traceback details:")
        # traceback.print_exc()
        continue

    time.sleep(2)
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


    #imageurl ='https://replicate.delivery/xezq/euk4pfC6JrqYLECcY9NokyRGQuoMRb29TBFbBfkatKpjGZ9oA/tmp2v21b5_0.png'
    time.sleep(2)
    response1a = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Is this text of date ["+block_of_text_user+"] in the image? Make sure the month is spelled correctly. Only replay with yes or no."},
                {
                "type": "image_url",
                "image_url": {
                    "url": imageurl,
                },
                },
            ],
            }
        ],
        max_tokens=300,
        )

    print(response1a.choices[0])

    reply1 = response1a.choices[0].message.content.lower()
    print(reply1)
    if reply1 == "yes":
        break
    print("Nooooo")
    
resize_and_crop(filename_raw, filename_final, input_width, input_height)

# delete the raw image

#os.remove(filename_raw)
#print(f"Deleted the raw image {filename_raw}")