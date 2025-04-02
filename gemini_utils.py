import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GeminiHandler:
    def __init__(self, api_key):
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        self.model = "gemini-2.0-flash"


    def generate_generic(self, contents, response_mime_type="text/plain"):
        generate_content_config = types.GenerateContentConfig(
            response_mime_type=response_mime_type,
        )

        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")






def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
