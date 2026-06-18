from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Message, Asset
from app.schemas.chat import ChatRequest, RefineRequest
from app.services.orchestrator import (
    classify_intent,
    handle_general_chat,
    extract_entities,
    extract_style_from_prompt
)
from app.services.prompt_service import enhance_prompt
from app.services.image_service import generate_image, refine_prompt
from app.services.asset_service import (
    create_asset,
    get_last_asset,
    get_user_style,
    update_user_style
)

router = APIRouter()


def get_history(db: Session, conversation_id: int) -> list:
    """Load previous messages as Mistral-compatible history."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str
):
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()


@router.post("/message")
def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    # Load conversation history
    history = get_history(db, req.conversation_id)

    # Feature 4: Load user style memory
    user_style = get_user_style(db, req.conversation_id)

    # Save user message
    save_message(db, req.conversation_id, "user", req.message)

    # Classify intent with history context
    intent = classify_intent(req.message, history)

    # ─── General Chat ────────────────────────────────────────────
    if intent == "general_chat":
        reply = handle_general_chat(req.message, history)
        save_message(db, req.conversation_id, "assistant", reply)
        return {
            "intent": intent,
            "reply": reply
        }

    # ─── Image Generation ────────────────────────────────────────
    if intent == "image_generation":

        # Feature 2: Extract entities to understand what user wants
        entities = extract_entities(
            req.message,
            history,
            user_style
        )

        # If request is unclear, ask for clarification
        # instead of blindly generating
        if not entities.get("is_clear"):
            question = entities.get(
                "clarification_needed",
                "Could you describe what you'd like to generate?"
            )
            save_message(
                db,
                req.conversation_id,
                "assistant",
                question
            )
            return {
                "intent": intent,
                "status": "clarification_needed",
                "question": question
            }

        # Use count from entities if user said "3 images"
        # otherwise fall back to req.count
        count = entities.get("count") or req.count

        # Build enriched prompt from extracted entities
        enriched_message = req.message
        if entities.get("style"):
            enriched_message += f", {entities['style']} style"
        if entities.get("mood"):
            enriched_message += f", {entities['mood']} mood"
        if entities.get("medium"):
            enriched_message += f", {entities['medium']}"
        if entities.get("colors"):
            enriched_message += f", {entities['colors']}"

        # Get N enhanced prompt variations
        enhanced_prompts = enhance_prompt(enriched_message, count=count)

        assets = []
        for prompt in enhanced_prompts:
            image_url = generate_image(prompt)
            asset = create_asset(
                db,
                req.conversation_id,
                image_url,
                prompt
            )
            assets.append({
                "asset_id": asset.id,
                "image_url": image_url,
                "prompt": prompt
            })

            # Feature 4: Extract and update user style memory
            # from each generated prompt
            style_data = extract_style_from_prompt(prompt)
            update_user_style(
                db,
                req.conversation_id,
                preferred_style=style_data.get("preferred_style"),
                preferred_mood=style_data.get("preferred_mood"),
                preferred_medium=style_data.get("preferred_medium"),
                preferred_colors=style_data.get("preferred_colors")
            )

        save_message(
            db,
            req.conversation_id,
            "assistant",
            f"Generated {len(assets)} image(s) based on: {req.message}"
        )

        return {
            "intent": intent,
            "count": len(assets),
            "assets": assets,
            # Show user what style was learned
            "style_learned": {
                "style": entities.get("style"),
                "mood": entities.get("mood"),
                "medium": entities.get("medium"),
                "colors": entities.get("colors")
            }
        }

    # ─── Image Refinement ────────────────────────────────────────
    if intent == "image_refinement":

        # Feature 1: Auto-detect last asset
        # no need for user to provide asset_id
        last_asset = get_last_asset(db, req.conversation_id)

        if not last_asset:
            reply = "I couldn't find a previous image to refine. Please generate an image first."
            save_message(db, req.conversation_id, "assistant", reply)
            return {
                "intent": intent,
                "status": "no_asset_found",
                "reply": reply
            }

        # Feature 2: Extract what user wants to change
        entities = extract_entities(req.message, history, user_style)

        assets = []
        count = entities.get("count") or req.count

        for i in range(count):
            new_prompt = refine_prompt(
                last_asset.prompt,
                req.message
            )
            image_url = generate_image(new_prompt)
            new_asset = create_asset(
                db,
                last_asset.conversation_id,
                image_url,
                new_prompt,
                version=last_asset.version + 1,
                parent_asset_id=last_asset.id
            )
            assets.append({
                "asset_id": new_asset.id,
                "image_url": image_url,
                "prompt": new_prompt,
                "version": new_asset.version
            })

            # Feature 4: Update style memory from refined prompt
            style_data = extract_style_from_prompt(new_prompt)
            update_user_style(
                db,
                req.conversation_id,
                preferred_style=style_data.get("preferred_style"),
                preferred_mood=style_data.get("preferred_mood"),
                preferred_medium=style_data.get("preferred_medium"),
                preferred_colors=style_data.get("preferred_colors")
            )

        save_message(
            db,
            req.conversation_id,
            "assistant",
            f"Refined image(s) based on: {req.message}"
        )

        return {
            "intent": intent,
            "parent_asset_id": last_asset.id,
            "count": len(assets),
            "assets": assets
        }

    # Fallback
    return {
        "intent": "unknown",
        "reply": "I didn't understand that. Could you rephrase?"
    }


@router.post("/refine")
def refine_image_endpoint(
    req: RefineRequest,
    db: Session = Depends(get_db)
):
    """
    Manual refine endpoint — user provides asset_id explicitly.
    Used when user wants to refine a specific older asset,
    not just the last one.
    """
    asset = (
        db.query(Asset)
        .filter(Asset.id == req.asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    assets = []
    for i in range(req.count):
        new_prompt = refine_prompt(asset.prompt, req.instruction)
        image_url = generate_image(new_prompt)
        new_asset = create_asset(
            db,
            asset.conversation_id,
            image_url,
            new_prompt,
            version=asset.version + 1,
            parent_asset_id=asset.id
        )
        assets.append({
            "asset_id": new_asset.id,
            "image_url": image_url,
            "prompt": new_prompt,
            "version": new_asset.version
        })

    return {
        "parent_asset_id": asset.id,
        "count": len(assets),
        "assets": assets
    }