from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime
)

from datetime import datetime
from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id")
    )

    role = Column(String)

    content = Column(Text)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(Integer)

    image_url = Column(Text)

    prompt = Column(Text)

    version = Column(Integer, default=1)

    parent_asset_id = Column(
        Integer,
        nullable=True
    )


class UserStyle(Base):
    __tablename__ = "user_styles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # links to a conversation
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        unique=True  # one style profile per conversation
    )

    preferred_style = Column(
        Text,
        nullable=True  # e.g. "dark, cinematic, oil painting"
    )

    preferred_mood = Column(
        Text,
        nullable=True  # e.g. "dramatic, melancholic"
    )

    preferred_medium = Column(
        Text,
        nullable=True  # e.g. "watercolor, digital art"
    )

    preferred_colors = Column(
        Text,
        nullable=True  # e.g. "warm tones, golden hour"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )