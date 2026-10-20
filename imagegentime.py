from openai import OpenAI
import requests
import datetime
import re


def make_filename_friendly(input_string):
    # Remove non-alphanumeric characters and replace spaces with underscores
    friendly_string = re.sub(r'\W+', '_', input_string.strip())

    # Get the current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # Append the date to the friendly string
    filename = f"{friendly_string}_{current_date}"

    return filename

client = OpenAI()

block_of_text_user ="10:05 PM"
filename = make_filename_friendly(block_of_text_user) + "_tb1.png"


block_of_text_system1 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

block_of_text_system2 = """
You are good in image text generation for a given input and describe the image. Make a closup and some pop. The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing pensils.
"""

block_of_text_system3 = """
You are good in image text generation for a given time of day and describe the image. Make a closup and some pop. Make it display the time in big digital text. The color palette is limited to black, white and red. The scene is cheerful and simplistic, emphasizing the contrast between the colors. Image on fit full resolution. No Drawing utensils.
"""

messages=[
    {"role": "system", "content": block_of_text_system3},
    {"role": "user", "content": block_of_text_user}
  ]

#model="gpt-4-1106-preview",
completion = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=messages
 
  
)
#print(completion.choices[0].message)

image_text = completion.choices[0].message.content
print(image_text)



#imagetext ="""
#Since I can't generate images, let's create a textual description of the image instead.\n\nPicture a simple, yet striking image that focuses on a horse. This is a close-up, so the horse's features are front and center, occupying most of the frame. Its mane is a deep, rich black, billowing softly as if caught in a gentle breeze. The horse's coat is a glossy white, almost shining, with the light hitting it in a way that it seems to gleam. Its eyes are a captivating, vibrant red, full of life and cheer.\n\nThe background is pure white, to emphasize the contrast and to keep the image minimalistic. Around the horse's head, there's a subtle red flare, which gives the image a bit of an ethereal glow. The flare is not overpowering but provides a warm, cheerful aura that complements the horse's own cheerfulness.\n\nDespite the limited color palette, the image feels full of life and joy, playing with the stark contrasts to create an engaging and simplistic visual that captivates the viewer
#"""
#size="1792x1024",
#standard
cnt1 = 0
while True:

    response = client.images.generate(
      model="dall-e-3",
      prompt=image_text,
      size="1024x1024",
      quality="standard",
      n=1,
    )

    image_url1 = response.data[0].url

    response1a = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {
          "role": "user",
          "content": [
            {"type": "text", "text": "Is this text of time "+block_of_text_user+" in the image? Only replay with yes or no."},
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
    #if response1a.choices[0].message.content

    #image_url2 = response.data[1].url
    #print(image_url)
    # save to file
    cnt1 += 1
    response5 = requests.get(image_url1)
    file1 = open("t"+ str(cnt1) + filename, "wb")
    file1.write(response5.content)
    file1.close()

    

    if response1a.choices[0].message.content == "Yes.":
        break
    
    if cnt1 > 2:
        break
    

print("Image saved to", filename)