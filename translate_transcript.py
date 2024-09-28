import re
import json
from tqdm import tqdm
from time import sleep
from openai import OpenAI
import openai

# Configure your OpenAI API key
openai_api_key = '<your-openai-api-key>'  # Replace with your OpenAI API key
client = OpenAI(api_key=openai_api_key)

def openai_json_gen(task, model="gpt-4o-mini"):
    valid = False
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": task}
    ]

    data = {}
    while not valid:
        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=messages,
            )

            data = json.loads(response.choices[0].message.content)
            valid = True
        except openai.APIError as e:
            print(f"OpenAI API returned an API Error: {e}")
            sleep(10)
        except openai.AuthenticationError as e:
            print(f"OpenAI API request was not authorized: {e}")
            return None
        except openai.RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            model = "gpt-3.5-turbo"
            sleep(360)
        except Exception as e:
            print(f"An exception occurred: {type(e).__name__}: {e}")
            sleep(1)

    return data


# Function to translate and format the text using the ChatGPT API
def translate_and_format_text(text):
    prompt = (
        f"Your goal is to format a YouTube video transcript. "
        f"If this transcript is in English, you will rewrite it in French. "
        f"If there are missing words or if the transcript is poorly written, you will rewrite it cleanly.\n\n"
        f"Here is the transcript: '{text}'\n\n"
        f"You will give me your response in JSON, which will be a dictionary with a single key 'result', containing the formatted transcript."
    )

    while True:
        result = openai_json_gen(prompt)
        if 'result' in result and isinstance(result['result'], str):
            result = result['result']
            break

    return result


# Read the content of the file
with open('final_output.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Split the content into text blocks based on YouTube video links
blocks = re.split(r'(https://www\.youtube\.com/watch\?v=[^\s]+)', content)

# Initialize the progress bar
progress_bar = tqdm(total=len(blocks) // 2, desc='Processing transcripts', unit='block')

# Rewrite the file with the translated content in French
with open('final_output_translated.txt', 'w', encoding='utf-8') as file:
    for i in range(1, len(blocks), 2):
        link = blocks[i]
        text = blocks[i + 1].strip() if i + 1 < len(blocks) else ""

        # Check if the text block is not empty
        if text:
            try:
                # Translate and format the text
                translated_text = translate_and_format_text(text)
            except Exception as e:
                # In case of an error, you can handle the exception here
                print(f"Error during translation: {e}")
                translated_text = text  # Use the original text in case of error

            # Write the link and the (translated and formatted) text into the file
            file.write(f"{link}\n{translated_text}\n")

        # Update the progress bar
        progress_bar.update(1)

# Close the progress bar
progress_bar.close()

print("The file has been successfully translated and rewritten.")
