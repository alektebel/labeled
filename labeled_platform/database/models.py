"""
Database models for the labeling platform.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
import secrets

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    wallet_address = Column(String(64), unique=True, index=True, nullable=False)

    # Stats
    total_labels = Column(Integer, default=0)
    correct_labels = Column(Integer, default=0)
    incorrect_labels = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    reputation_score = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relationships
    labels = relationship("Label", back_populates="user")
    sessions = relationship("LabelingSession", back_populates="user")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def generate_wallet_address() -> str:
        """Generate a unique wallet address."""
        return hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:42]

    def verify_password(self, password: str) -> bool:
        """Verify password."""
        return self.password_hash == self.hash_password(password)

    def update_stats(self, is_correct: bool):
        """Update user statistics."""
        self.total_labels += 1
        if is_correct:
            self.correct_labels += 1
        else:
            self.incorrect_labels += 1

        if self.total_labels > 0:
            self.accuracy = self.correct_labels / self.total_labels
            # Reputation = accuracy weighted by volume
            self.reputation_score = self.accuracy * min(self.total_labels / 100, 1.0)


class DataItem(Base):
    """Data item to be labeled."""
    __tablename__ = "data_items"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True)
    item_type = Column(String(50), nullable=False)  # image, text, audio, video
    data_url = Column(Text, nullable=False)  # URL or path to data

    # Metadata
    metadata = Column(JSON, default={})
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Labeling info
    required_labels = Column(Integer, default=5)  # Min labels needed for consensus
    consensus_label = Column(String(100), nullable=True)
    consensus_confidence = Column(Float, nullable=True)
    has_consensus = Column(Boolean, default=False)

    # Relationships
    labels = relationship("Label", back_populates="data_item")


class Label(Base):
    """Individual label submission."""
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_item_id = Column(Integer, ForeignKey("data_items.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("labeling_sessions.id"), nullable=True)

    # Label data
    label_value = Column(String(200), nullable=False)
    confidence = Column(Float, default=1.0)
    time_spent = Column(Float, nullable=True)  # seconds

    # Validation
    is_validated = Column(Boolean, default=False)
    is_correct = Column(Boolean, nullable=True)
    reward_amount = Column(Float, default=0.0)
    penalty_amount = Column(Float, default=0.0)

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, default={})

    # Relationships
    user = relationship("User", back_populates="labels")
    data_item = relationship("DataItem", back_populates="labels")
    session = relationship("LabelingSession", back_populates="labels")


class LabelingSession(Base):
    """Labeling session tracking."""
    __tablename__ = "labeling_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session info
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    items_labeled = Column(Integer, default=0)

    # Performance
    total_rewards = Column(Float, default=0.0)
    total_penalties = Column(Float, default=0.0)
    session_accuracy = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="sessions")
    labels = relationship("Label", back_populates="session")
