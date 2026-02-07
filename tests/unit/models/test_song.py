from vibe_dj.models.song import Song


def test_song_creation():
    """Test creating a Song instance."""
    song = Song(
        id=1,
        file_path="/path/to/song.mp3",
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        genre="Rock",
        last_modified=1234567890.0,
        duration=180,
    )

    assert song.id == 1
    assert song.title == "Test Song"
    assert song.artist == "Test Artist"
    assert song.duration == 180


def test_song_str():
    song = Song(
        id=1,
        file_path="/path/to/song.mp3",
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        genre="Rock",
        last_modified=1234567890.0,
        duration=180,
    )

    assert str(song) == "Test Artist - Test Song"


def test_song_with_none_values():
    song = Song(
        id=1,
        file_path="/path/to/song.mp3",
        title="Test Song",
        artist="Test Artist",
        album="Unknown",
        genre="Unknown",
        last_modified=1234567890.0,
        duration=None,
    )

    assert song.duration is None
