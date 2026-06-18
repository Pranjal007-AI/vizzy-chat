from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Asset, UserStyle


def create_asset(
    db: Session,
    conversation_id: int,
    image_url: str,
    prompt: str,
    version: int = 1,
    parent_asset_id: int = None
) -> Asset:
    asset = Asset(
        conversation_id=conversation_id,
        image_url=image_url,
        prompt=prompt,
        version=version,
        parent_asset_id=parent_asset_id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_last_asset(
    db: Session,
    conversation_id: int
) -> Asset | None:
    return (
        db.query(Asset)
        .filter(Asset.conversation_id == conversation_id)
        .order_by(Asset.id.desc())
        .first()
    )


def get_user_style(
    db: Session,
    conversation_id: int
) -> UserStyle | None:
    return (
        db.query(UserStyle)
        .filter(UserStyle.conversation_id == conversation_id)
        .first()
    )


def update_user_style(
    db: Session,
    conversation_id: int,
    preferred_style=None,
    preferred_mood=None,
    preferred_medium=None,
    preferred_colors=None
) -> UserStyle:

    # Convert lists to comma-separated strings
    if isinstance(preferred_style, list):
        preferred_style = ", ".join(preferred_style)
    if isinstance(preferred_mood, list):
        preferred_mood = ", ".join(preferred_mood)
    if isinstance(preferred_medium, list):
        preferred_medium = ", ".join(preferred_medium)
    if isinstance(preferred_colors, list):
        preferred_colors = ", ".join(preferred_colors)

    style = get_user_style(db, conversation_id)

    if not style:
        style = UserStyle(
            conversation_id=conversation_id,
            preferred_style=preferred_style,
            preferred_mood=preferred_mood,
            preferred_medium=preferred_medium,
            preferred_colors=preferred_colors,
            updated_at=datetime.utcnow()
        )
        db.add(style)
    else:
        if preferred_style:
            style.preferred_style = preferred_style
        if preferred_mood:
            style.preferred_mood = preferred_mood
        if preferred_medium:
            style.preferred_medium = preferred_medium
        if preferred_colors:
            style.preferred_colors = preferred_colors
        style.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(style)
    return style