# hello_llm.py
import os                          # Built-in Python module for reading environment variables
from dotenv import load_dotenv     # Loads environment variables from the .env file
import openai                      # Official OpenAI SDK for calling AI models

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise SystemExit("OPENROUTER_API_KEY is missing. Add it to .env and try again.")                      # Read the API Key from the .env file

client = openai.OpenAI(            # Create a "client" object
    base_url="https://openrouter.ai/api/v1",   # Point it at OpenRouter
    api_key=api_key,    # Read the Key from .env
)

response = client.chat.completions.create(      # Send the request to the AI
    model="deepseek/deepseek-v4-flash-0731",        # Which model to use
    messages=[                                   # The conversation content
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python in 2 sentences? "}
    ],
    temperature=1.0,                            # <-- the new parameter to control randomness
)

print(response.choices[0].message.content)      # Extract and print the AI's answer

print("\n--- Details ---")
print(f"Model: {response.model}")
print(f"Prompt tokens:     {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens:      {response.usage.total_tokens}")
