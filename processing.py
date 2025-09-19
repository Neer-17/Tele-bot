import base64
from dotenv import load_dotenv
from groq import Groq
import os
import requests
import json
from requests.structures import CaseInsensitiveDict
load_dotenv()
groq_api_key = os.environ.get("groq_api_key")
geo_api_key = os.environ.get("geo_api_key")
def encode_image(image_path):
    '''Encodes an image file to a base64 string.'''
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_document_with_llama_vision(image_path, groq_api_key):
    '''Analyzes an image using Groq's Llama Vision model and returns the analysis.'''
    client = Groq(api_key=groq_api_key)
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct", # Use a supported vision model
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """You are an assistant that analyzes civic issues from photos. 
The user will upload a photo of their surroundings (e.g., roads, public spaces, infrastructure). 
Your task is:

1. Identify if there is a visible civic problem (examples: trash pile, pothole, broken streetlight, waterlogging, damaged footpath, illegal parking, stray animals).
2. Provide a clear and concise summary of the issue in one or two sentences, suitable for a tweet.
3. Be objective and polite, avoiding offensive language. 
4. If no clear civic issue is visible, respond with: "No obvious civic issue detected."

Format your output in JSON:
{
  "problem_detected": "<yes/no>",
  "problem_type": "<short label like 'garbage', 'pothole', 'streetlight'>",
  "summary": "<A DETAILED ANALYSIS OF THE IMAGE,PLACE,ISSUE AND ITS SURROUNDINGS>"
}"""                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "text"}
    )
    return response.choices[0].message.content


def address_to_location(location):
    '''Converts latitude and longitude to a human-readable address using Geoapify API.'''
    url = f"https://api.geoapify.com/v1/geocode/reverse?lat={location['latitude']}&lon={location['longitude']}&apiKey={geo_api_key}"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)
    loc_bytes = resp.content
    loc_decoded = loc_bytes.decode('utf-8')
    loc = json.loads(loc_decoded)
    address = loc['features'][0]['properties']['formatted']
    return address


def content(summary,location,groq_api_key):
    '''Generates a tweet based on the summary and location using Groq's language model.'''
    # print(f"Generating tweet with summary: {summary} and location: {location['latitude']}+{location['longitude']}")
    client = Groq(api_key=groq_api_key)
    summary = eval(summary)
    address = address_to_location(location)
    # print(f"Resolved address: {address}")
    # print(f"Raw summary inside content function: {summary}")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [
    {
        "role": "user",
        "content": f"""
You are an assistant that drafts concise, strong tweets to report civic problems. 
You will receive:
- A short summary of the issue
- The problem type
- Location details (optional)

Your task:
1. Write a clear and respectful tweet (about 250 characters).
2. Ensure the tweet is criticizing,firm, and community-oriented.
3. Include the responsible government handles of the given address naturally in the text (can include more than one depending on the issue).
4. If a maps link or coordinates are given, add them at the end (this is the examplae of the map link, use this format "https://www.google.com/maps/place/{location['latitude']}+{location['longitude']}").


Format output as plain text with no extra commentary.

Summary: {summary['summary']}
Problem Type: {summary['problem_type']}
Location: {location}
address: {address if address else "Not provided"}
"""
    }
]
    )
    tweet = response.choices[0].message.content
    print(tweet)
    return tweet
