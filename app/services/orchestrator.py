from mistralai import Mistral
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def classify_intent(message: str, history: list = []) -> str:
    classify_prompt = f"""
Classify this request. Analyze the user's message carefully.

Return ONLY one of these exact words:

image_generation - if the user wants to create, generate, or make an image
image_refinement - if the user wants to edit, refine, or modify an existing image
general_chat - if the user is just chatting, asking questions, or anything else

Request:
{message}
"""
    messages = history + [{"role": "user", "content": classify_prompt}]

    response = client.chat.complete(
        model="mistral-small-2503",
        messages=messages
    )

    intent = response.choices[0].message.content.strip().lower()

    valid_intents = ["image_generation", "image_refinement", "general_chat"]
    if intent not in valid_intents:
        return "general_chat"

    return intent


def handle_general_chat(message: str, history: list = []) -> str:
    messages = history + [{"role": "user", "content": message}]

    response = client.chat.complete(
        model="mistral-small-2503",
        messages=messages
    )

    return response.choices[0].message.content.strip()


# ─── Feature 2: Understand what user wants ──────────────────────

def extract_entities(
    message: str,
    history: list = [],
    user_style: object = None
) -> dict:
    """
    Before generating anything, extract structured
    information from the user's message.

    Returns a dict like:
    {
        "subject": "a sunset over mountains",
        "style": "oil painting",
        "mood": "dramatic",
        "medium": "digital art",
        "colors": "warm golden tones",
        "count": 1,
        "is_clear": true,
        "clarification_needed": null
    }
    """

    # Build style context if user has preferences
    style_context = ""
    if user_style:
        style_context = f"""
The user has these known preferences:
- Style: {user_style.preferred_style or 'not set'}
- Mood: {user_style.preferred_mood or 'not set'}
- Medium: {user_style.preferred_medium or 'not set'}
- Colors: {user_style.preferred_colors or 'not set'}

Apply these preferences if the user hasn't specified otherwise.
"""

    extract_prompt = f"""
You are an AI that extracts structured information from image generation requests.

{style_context}

Analyze the user's message and return ONLY a valid JSON object with these fields:
{{
    "subject": "what to draw/generate (null if unclear)",
    "style": "art style if mentioned (null if not mentioned)",
    "mood": "emotional tone if mentioned (null if not mentioned)",
    "medium": "artistic medium if mentioned (null if not mentioned)",
    "colors": "color preferences if mentioned (null if not mentioned)",
    "count": 1,
    "is_clear": true or false,
    "clarification_needed": "question to ask user if unclear (null if clear)"
}}

Rules:
- If the request is too vague (e.g. "paint something"), set is_clear to false
- If is_clear is false, set clarification_needed to a helpful question
- count should be the number of images requested (default 1)
- Return ONLY the JSON, no extra text

User message: {message}
"""

    messages = history + [{"role": "user", "content": extract_prompt}]

    response = client.chat.complete(
        model="mistral-small-2503",
        messages=messages
    )

    raw = response.choices[0].message.content.strip()

    # Clean markdown if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "subject": message,
            "style": None,
            "mood": None,
            "medium": None,
            "colors": None,
            "count": 1,
            "is_clear": True,
            "clarification_needed": None
        }


# ─── Feature 4: Extract style from generated prompt ─────────────

def extract_style_from_prompt(prompt: str) -> dict:
    """
    After generating an image, extract style preferences
    from the enhanced prompt to update user style memory.
    """
    extract_prompt = f"""
Analyze this image generation prompt and extract style information.
Return ONLY a valid JSON object:
{{
    "preferred_style": "overall art style (null if not found)",
    "preferred_mood": "emotional tone (null if not found)",
    "preferred_medium": "artistic medium (null if not found)",
    "preferred_colors": "color palette (null if not found)"
}}

Prompt: {prompt}
"""

    response = client.chat.complete(
        model="mistral-small-2503",
        messages=[{"role": "user", "content": extract_prompt}]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "preferred_style": None,
            "preferred_mood": None,
            "preferred_medium": None,
            "preferred_colors": None
        }