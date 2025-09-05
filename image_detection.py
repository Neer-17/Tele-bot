import base64
from dotenv import load_dotenv
from groq import Groq
import os
load_dotenv()
groq_api_key = os.environ.get("groq_api_key")
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_document_with_llama_vision(image_path, groq_api_key):
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
        response_format={"type": "json_object"}
    )
    print(response.choices[0].message.content
)
    return response.choices[0].message.content

# Example usage:
# groq_api_key = os.environ.get("GROQ_API_KEY")
# json_output = analyze_document_with_llama_vision("path_to_your_document.jpg", groq_api_key)
# print(json_output)