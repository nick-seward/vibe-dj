from datetime import datetime

import pytest

from vibe_dj.models.playlist import Playlist
from vibe_dj.models.song import Song


class TestPlaylist:
    """Test suite for Playlist model."""

    @pytest.fixture()
    def sample_songs(self):
        """Set up test fixtures with sample songs before each test method."""
        song1 = Song(
            id=1,
            file_path="/path/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/path/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        return song1, song2

    def test_playlist_creation(self):
        playlist = Playlist()

        assert len(playlist) == 0
        assert len(playlist.songs) == 0
        assert len(playlist.seed_songs) == 0
        assert isinstance(playlist.created_at, datetime)

    def test_add_song(self, sample_songs):
        song1, _song2 = sample_songs
        playlist = Playlist()
        playlist.add_song(song1)

        assert len(playlist) == 1
        assert playlist.songs[0] == song1

    def test_add_multiple_songs(self, sample_songs):
        song1, song2 = sample_songs
        playlist = Playlist()
        playlist.add_song(song1)
        playlist.add_song(song2)

        assert len(playlist) == 2
        assert playlist.songs[0] == song1
        assert playlist.songs[1] == song2

    def test_remove_song(self, sample_songs):
        song1, song2 = sample_songs
        playlist = Playlist(songs=[song1, song2])

        result = playlist.remove_song(1)

        assert result
        assert len(playlist) == 1
        assert playlist.songs[0] == song2

    def test_remove_nonexistent_song(self, sample_songs):
        song1, _song2 = sample_songs
        playlist = Playlist(songs=[song1])

        result = playlist.remove_song(999)

        assert not result
        assert len(playlist) == 1

    def test_get_song_ids(self, sample_songs):
        song1, song2 = sample_songs
        playlist = Playlist(songs=[song1, song2])

        song_ids = playlist.get_song_ids()

        assert song_ids == [1, 2]

    def test_playlist_with_seeds(self, sample_songs):
        song1, song2 = sample_songs
        playlist = Playlist(songs=[song2], seed_songs=[song1])

        assert len(playlist.songs) == 1
        assert len(playlist.seed_songs) == 1
        assert playlist.seed_songs[0] == song1
