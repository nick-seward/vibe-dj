import json
import tempfile
from pathlib import Path

import pytest

from vibe_dj.models import Config, Playlist, Song
from vibe_dj.services.playlist_exporter import PlaylistExporter


@pytest.fixture()
def exporter_setup():
    config = Config()
    exporter = PlaylistExporter(config)

    song1 = Song(
        id=1,
        file_path="/music/song1.mp3",
        title="Song 1",
        artist="Artist 1",
        album="Album 1",
        genre="Rock",
        last_modified=0.0,
        duration=180,
    )
    song2 = Song(
        id=2,
        file_path="/music/song2.mp3",
        title="Song 2",
        artist="Artist 2",
        album="Album 2",
        genre="Pop",
        last_modified=0.0,
        duration=200,
    )

    playlist = Playlist(songs=[song1, song2], seed_songs=[song1])
    return exporter, playlist


def test_export_m3u(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export_m3u(playlist, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "#EXTM3U" in content
        assert "Artist 1 - Song 1" in content
        assert "Artist 2 - Song 2" in content
        assert "/music/song1.mp3" in content
        assert "/music/song2.mp3" in content
        assert "#EXTINF:180" in content
        assert "#EXTINF:200" in content
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_m3u_with_none_duration(exporter_setup):
    exporter, _playlist = exporter_setup
    song_no_duration = Song(
        id=3,
        file_path="/music/song3.mp3",
        title="Song 3",
        artist="Artist 3",
        album="Album 3",
        genre="Rock",
        last_modified=0.0,
        duration=None,
    )
    playlist = Playlist(songs=[song_no_duration])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export_m3u(playlist, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "#EXTINF:-1" in content
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_m3u8(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u8", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export_m3u8(playlist, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "#EXTM3U" in content
        assert "Artist 1 - Song 1" in content
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_json(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export_json(playlist, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "created_at" in data
        assert "seed_songs" in data
        assert "songs" in data
        assert len(data["songs"]) == 2
        assert len(data["seed_songs"]) == 1
        assert data["songs"][0]["title"] == "Song 1"
        assert data["songs"][0]["artist"] == "Artist 1"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_with_format_m3u(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export(playlist, temp_path, output_format="m3u")

        assert Path(temp_path).exists()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_with_format_json(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        exporter.export(playlist, temp_path, output_format="json")

        with open(temp_path, "r") as f:
            data = json.load(f)

        assert "songs" in data
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_unsupported_format(exporter_setup):
    exporter, playlist = exporter_setup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            exporter.export(playlist, temp_path, output_format="txt")
    finally:
        Path(temp_path).unlink(missing_ok=True)
