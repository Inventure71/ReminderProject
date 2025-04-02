import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import base64
import os
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

class GeminiHandler:
    def __init__(self, api_key):
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        self.model = "gemini-2.0-flash"


    def generate_generic(self, contents, response_mime_type="text/plain", streaming=False):
        generate_content_config = types.GenerateContentConfig(
            response_mime_type=response_mime_type,
        )

        if streaming:
            response = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                print(chunk.text, end="")
                response += chunk.text
            return response

        else:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            return response.text

    def classify_messages(self, messages, projects):

        new_messages = self.split_into_chunks(messages, extra=projects)
        print("Classifying messages", new_messages)

        total_response = []

        for chunk in new_messages:

            prompt = f"""
            
            messages: {chunk}
            
            """

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["messages"],
                    properties={
                        "messages": genai.types.Schema(
                            type=genai.types.Type.ARRAY,
                            items=genai.types.Schema(
                                type=genai.types.Type.OBJECT,
                                required=["index of the message", "project"],
                                properties={
                                    "index of the message": genai.types.Schema(
                                        type=genai.types.Type.INTEGER,
                                    ),
                                    "project": genai.types.Schema(
                                        type=genai.types.Type.STRING,
                                    ),
                                    "reminder time": genai.types.Schema(
                                        type=genai.types.Type.STRING,
                                    ),
                                },
                            ),
                        ),
                    },
                ),
                system_instruction=[
                    types.Part.from_text(text="""Your job is to analize each message (more thane might be provided) and check if they belong to any of the following categories:
            minder, in this case specify the timestamp of when to remind YYYY-MM-DD HH:MM:SS, if it something that the user should remeber but it has no remind time than set the time as the day after at 20:00 
             idea, in that case add the message to the project IDEAS
    
            are going to be provided all the projects that have already been created and the top messages from that project, use them as context to understand if a message should be part of that project, if the message is not part of any project just write NULL in the project field."""),
                ],
            )

            response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config,
            )

            print(response.text)

            total_response.append(response.text)

        return total_response

    def split_into_chunks(self, text, extra="", chunk_size=16384):
        """
        Split the input text into chunks of a specified size while going line by line, if an extra string is given remove the length of that string from all blocks (they should now be shorter).
        """
        # Calculate effective chunk size considering the extra string
        effective_chunk_size = chunk_size - len(extra)
        if effective_chunk_size <= 0:
            raise ValueError("Extra text is too long for the given chunk size")

        # Handle empty text case
        if not text:
            return []

        # Split the text into lines
        lines = text if isinstance(text, list) else text.split('\n')

        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)

            # If adding this line would exceed the chunk size, start a new chunk
            if current_size + line_size > effective_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            # If a single line is larger than the chunk size, we need to split it
            if line_size > effective_chunk_size:
                # If there's content in the current chunk, add it to chunks
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split the long line into multiple chunks
                for i in range(0, len(line), effective_chunk_size):
                    chunks.append(line[i:i + effective_chunk_size])
            else:
                # Add the line to the current chunk
                current_chunk.append(line)
                current_size += line_size + 1  # +1 for the newline character

        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks




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
