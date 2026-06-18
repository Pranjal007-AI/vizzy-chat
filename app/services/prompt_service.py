from mistralai import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def enhance_prompt(prompt: str, count: int = 1) -> list[str]:
    """
    Returns `count` enhanced prompt variations.
    """
    response = client.chat.complete(
        model="mistral-small-2503",
        messages=[
            {
                "role": "system",
                "content": f"""
You are a creative image prompt enhancer.
The user wants {count} image variation(s).
Generate exactly {count} enhanced prompt(s) for image generation.
Return ONLY a numbered list like:
1. <prompt one>
2. <prompt two>
No extra text, no explanations.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Parse numbered list into a Python list
    lines = raw.split("\n")
    prompts = []
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit():
            # Remove "1. " prefix
            cleaned = line.split(".", 1)[-1].strip()
            prompts.append(cleaned)

    # Fallback if parsing fails
    if not prompts:
        prompts = [raw]

    return prompts[:count]