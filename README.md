# Image Generation Script using OpenAI and Replicate

This Python script generates images based on user-provided text prompts. It leverages OpenAI's GPT model to create detailed image descriptions and uses Replicate's image generation models to produce the final images.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Example](#example)
- [Functions Explained](#functions-explained)
- [Customization](#customization)
- [Notes](#notes)
- [License](#license)

## Features
- **Text to Image Description**: Converts user input into a detailed image description using OpenAI's GPT model
- **Image Generation**: Creates images based on the generated descriptions using Replicate's models
- **Custom Resolution Handling**: Resizes images to custom dimensions while maintaining aspect ratio within specified bounds
- **Filename Sanitization**: Generates filename-friendly strings based on input text and the current date
- **Base64 Image Decoding**: Handles base64-encoded images and saves them as PNG files

## Prerequisites
- Python 3.6+
- API Keys:
  - OpenAI API Key: Obtain from OpenAI
  - Replicate API Token: Obtain from Replicate

## Installation

### Install Dependencies:
```bash
pip install openai replicate pillow requests
```

### Set Environment Variables:
Configure your API keys as environment variables.

On Linux/macOS:
```bash
export OPENAI_API_KEY='your-openai-api-key'
export REPLICATE_API_TOKEN='your-replicate-api-token'
```

On Windows:
```cmd
set OPENAI_API_KEY=your-openai-api-key
set REPLICATE_API_TOKEN=your-replicate-api-token
```

## Usage

### Modify Input Text:
Open `imagegen.py` and set your desired input text:
```python
block_of_text_user = "Your desired image prompt here"
```

### Set Image Dimensions:
Adjust the desired image width and height:
```python
input_width, input_height = desired_width, desired_height
```

### Run the Script:
```bash
python imagegen.py
```

### Output:
- The script will generate an image based on your input text
- The final image will be saved with a filename derived from your input text and the current timestamp
- The image will be resized to your specified dimensions

## Example

Suppose you set:
```python
block_of_text_user = "Majestic mountain landscape"
input_width, input_height = 1024, 768
```

**Process:**
1. The script generates an image description for "Majestic mountain landscape" using OpenAI's GPT model
2. It then uses Replicate's image generation model to create an image based on that description
3. The image is saved as `Majestic_mountain_landscape_YYYYMMDD_HHMMSS_f1.png`

## Functions Explained

### `make_filename_friendly(input_string)`
Converts the input string into a filename-friendly format by removing non-alphanumeric characters, replacing spaces with underscores, and appending the current date and time.

### `resize_resolution(width, height, min_size=256, max_size=1440)`
Calculates new image dimensions to ensure they are within the specified minimum and maximum size bounds while maintaining the aspect ratio.

### `resize_png(input_path, output_path, new_width, new_height)`
Resizes a PNG image to the specified dimensions using high-quality resampling.

### `save_base64_as_png(data_url, file_name="output.png")`
Decodes a base64-encoded PNG image and saves it as a file.

## Customization

### System Prompts:
The script uses system prompts to guide the image description generation. You can customize these prompts to change the style or content of the generated images.

```python
block_of_text_system1 = """
Customize this prompt to influence the image description.
"""
```

### Model Selection:

**OpenAI Model**: The script uses the "gpt-4o-mini" model. Ensure you have access to this model or replace it with another available model.
```python
completion = client.chat.completions.create(
  model="your-model-choice",
  messages=messages
)
```

**Replicate Model**: Adjust the model or its parameters as needed.
```python
output = replicate.run(
    "your-replicate-model",
    input={...},
    timeout=120
)
```

### Image Quality Settings:
Modify the `output_quality`, `safety_tolerance`, and other parameters in the `replicate.run` function to fine-tune the image generation process.

## Notes

### Error Handling:
- The script includes checks to handle cases where the image generation fails or returns unexpected data
- If the image cannot be downloaded or saved, an error message will be printed

### Dependencies:
- Ensure all required libraries are installed and up to date
- The script assumes that the OpenAI and Replicate libraries are correctly configured with your API keys

### File Management:
- The raw image file (`filename_raw`) is deleted after resizing to conserve disk space
- The final image is saved with a filename that includes the sanitized input text and a timestamp

## License
This project is licensed under the MIT License. See the LICENSE file for details.
