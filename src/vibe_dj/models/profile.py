"""SQLAlchemy model for user profiles with Subsonic credentials."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Profile(Base):
    """Represents a user profile with optional Subsonic credentials.

    Profiles enable per-user Subsonic credentials in a shared household
    environment. The 'shared' profile is created by default and cannot
    be deleted.
    """

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(String, unique=True)
    subsonic_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subsonic_username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subsonic_password_encrypted: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __str__(self) -> str:
        """Return human-readable string representation.

        :return: String showing the profile display name
        """
        return self.display_name

    def __repr__(self) -> str:
        """Return detailed string representation for debugging.

        :return: String showing id and display_name
        """
        return f"Profile(id={self.id}, display_name='{self.display_name}')"
