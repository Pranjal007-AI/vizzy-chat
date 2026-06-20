from mistralai import Mistral
from dotenv import load_dotenv
import os
import uuid
from huggingface_hub import InferenceClient

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

HF_API_KEY = os.getenv("HF_API_KEY")
hf_client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "static", "generated"
)
os.makedirs(STATIC_DIR, exist_ok=True)


def generate_image(prompt: str) -> str:
    """
    Generate a real AI image using Hugging Face Inference Providers
    (FLUX.1-schnell). Saves locally and returns a servable URL.
    """
    image = hf_client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-schnell",
    )

    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(STATIC_DIR, filename)
    image.save(filepath)

    return f"{BASE_URL}/static/generated/{filename}"


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