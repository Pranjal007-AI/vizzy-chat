from mistralai import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def generate_image(prompt: str) -> str:
    safe_prompt = (
        prompt[:40]
        .replace(" ", "+")
    )
    return (
        f"https://dummyimage.com/"
        f"1024x1024/000/fff"
        f"&text={safe_prompt}"
    )


def refine_prompt(
    original_prompt: str,
    instruction: str
) -> str:
    response = client.chat.complete(
        model="mistral-small-2503",
        messages=[
            {
                "role": "system",
                "content": """
You are an expert image prompt editor.
Modify the prompt based on the instruction.
Preserve original composition.
Return ONLY the updated prompt, no extra text.
"""
            },
            {
                "role": "user",
                "content": f"Original: {original_prompt}\nInstruction: {instruction}"
            }
        ]
    )
    return response.choices[0].message.content.strip()