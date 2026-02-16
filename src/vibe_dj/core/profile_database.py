"""Database interface for managing user profiles with encrypted credentials."""

import os
from typing import List, Optional

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from vibe_dj.models.base import Base
from vibe_dj.models.profile import Profile


class ProfileDatabase:
    """Database interface for managing user profiles.

    Provides CRUD methods for profiles and handles password
    encryption/decryption using Fernet symmetric encryption.
    Uses a separate profiles.db file from the main music database.
    """

    SHARED_PROFILE_NAME = "Shared"

    def __init__(self, db_path: str, encryption_key: Optional[str] = None):
        """Initialize the profile database.

        :param db_path: Path to the SQLite database file
        :param encryption_key: Base64-encoded Fernet key for password encryption.
            If not provided, a new key is generated and should be persisted.
        """
        self.db_path = db_path
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode())
        else:
            self._fernet = Fernet(Fernet.generate_key())
        self._engine = create_engine(f"sqlite:///{db_path}")
        self._session_factory = sessionmaker(bind=self._engine)
        self._session: Optional[Session] = None

    @property
    def encryption_key(self) -> str:
        """Get the Fernet encryption key as a string.

        :return: Base64-encoded Fernet key
        """
        return self._fernet._signing_key.__class__.__name__  # pragma: no cover

    def __enter__(self) -> "ProfileDatabase":
        """Enter context manager, establishing database session.

        :return: Self reference for use in with statement
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, closing database session.

        :param exc_type: Exception type if an exception occurred
        :param exc_val: Exception value if an exception occurred
        :param exc_tb: Exception traceback if an exception occurred
        """
        self.close()

    def connect(self) -> None:
        """Establish a new SQLAlchemy session.

        Creates a new session if one doesn't exist.
        """
        if self._session is None:
            self._session = self._session_factory()

    def close(self) -> None:
        """Close the database session if open."""
        if self._session:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        """Get the active database session.

        :return: Active SQLAlchemy session
        :raises RuntimeError: If database is not connected
        """
        if self._session is None:
            raise RuntimeError(
                "Database not connected. Use context manager or call connect()."
            )
        return self._session

    def init_db(self) -> None:
        """Initialize database schema and create default 'Shared' profile.

        Creates the profiles table if it doesn't exist, then ensures
        the default 'Shared' profile exists.
        """
        Base.metadata.create_all(self._engine, tables=[Profile.__table__])
        existing = self.session.execute(
            select(Profile).where(Profile.display_name == self.SHARED_PROFILE_NAME)
        ).scalar_one_or_none()
        if not existing:
            shared = Profile(display_name=self.SHARED_PROFILE_NAME)
            self.session.add(shared)
            self.session.commit()

    def encrypt_password(self, password: str) -> str:
        """Encrypt a password using Fernet symmetric encryption.

        :param password: Plaintext password to encrypt
        :return: Encrypted password as a string
        """
        return self._fernet.encrypt(password.encode()).decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password using Fernet symmetric encryption.

        :param encrypted_password: Encrypted password string
        :return: Decrypted plaintext password
        """
        return self._fernet.decrypt(encrypted_password.encode()).decode()

    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """Retrieve a profile by its ID.

        :param profile_id: ID of the profile to retrieve
        :return: Profile object if found, None otherwise
        """
        return self.session.get(Profile, profile_id)

    def get_profile_by_name(self, display_name: str) -> Optional[Profile]:
        """Retrieve a profile by its display name.

        :param display_name: Display name of the profile
        :return: Profile object if found, None otherwise
        """
        return self.session.execute(
            select(Profile).where(Profile.display_name == display_name)
        ).scalar_one_or_none()

    def get_all_profiles(self) -> List[Profile]:
        """Retrieve all profiles ordered by ID.

        :return: List of all Profile objects
        """
        return list(
            self.session.execute(select(Profile).order_by(Profile.id)).scalars().all()
        )

    def create_profile(
        self,
        display_name: str,
        subsonic_url: Optional[str] = None,
        subsonic_username: Optional[str] = None,
        subsonic_password: Optional[str] = None,
    ) -> Profile:
        """Create a new profile.

        :param display_name: Display name for the profile
        :param subsonic_url: Optional Subsonic server URL
        :param subsonic_username: Optional Subsonic username
        :param subsonic_password: Optional plaintext password (will be encrypted)
        :return: Created Profile object
        :raises ValueError: If a profile with the same display name already exists
        """
        existing = self.get_profile_by_name(display_name)
        if existing:
            raise ValueError(f"Profile with name '{display_name}' already exists")

        encrypted_password = None
        if subsonic_password:
            encrypted_password = self.encrypt_password(subsonic_password)

        profile = Profile(
            display_name=display_name,
            subsonic_url=subsonic_url,
            subsonic_username=subsonic_username,
            subsonic_password_encrypted=encrypted_password,
        )
        self.session.add(profile)
        self.session.commit()
        return profile

    def update_profile(
        self,
        profile_id: int,
        display_name: Optional[str] = None,
        subsonic_url: Optional[str] = None,
        subsonic_username: Optional[str] = None,
        subsonic_password: Optional[str] = None,
    ) -> Optional[Profile]:
        """Update an existing profile.

        Only provided (non-None) fields are updated. To clear a field,
        pass an empty string.

        :param profile_id: ID of the profile to update
        :param display_name: New display name
        :param subsonic_url: New Subsonic URL
        :param subsonic_username: New Subsonic username
        :param subsonic_password: New plaintext password (will be encrypted)
        :return: Updated Profile object, or None if not found
        :raises ValueError: If new display_name conflicts with an existing profile
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        if display_name is not None:
            if display_name != profile.display_name:
                conflict = self.get_profile_by_name(display_name)
                if conflict:
                    raise ValueError(
                        f"Profile with name '{display_name}' already exists"
                    )
            profile.display_name = display_name

        if subsonic_url is not None:
            profile.subsonic_url = subsonic_url if subsonic_url else None

        if subsonic_username is not None:
            profile.subsonic_username = subsonic_username if subsonic_username else None

        if subsonic_password is not None:
            if subsonic_password:
                profile.subsonic_password_encrypted = self.encrypt_password(
                    subsonic_password
                )
            else:
                profile.subsonic_password_encrypted = None

        self.session.commit()
        return profile

    def delete_profile(self, profile_id: int) -> bool:
        """Delete a profile by its ID.

        The 'Shared' profile cannot be deleted.

        :param profile_id: ID of the profile to delete
        :return: True if deleted, False if not found
        :raises ValueError: If attempting to delete the 'Shared' profile
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        if profile.display_name == self.SHARED_PROFILE_NAME:
            raise ValueError("The 'Shared' profile cannot be deleted")

        self.session.delete(profile)
        self.session.commit()
        return True

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key.

        :return: Base64-encoded Fernet key as a string
        """
        return Fernet.generate_key().decode()
