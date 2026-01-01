import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from vibe_dj.services.playlist_exporter import PlaylistExporter
from vibe_dj.models import Config, Playlist, Song


class TestPlaylistExporter(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.exporter = PlaylistExporter(self.config)
        
        self.song1 = Song(
            id=1, file_path="/music/song1.mp3", title="Song 1", artist="Artist 1",
            genre="Rock", mbid=None, last_modified=0.0, duration=180
        )
        self.song2 = Song(
            id=2, file_path="/music/song2.mp3", title="Song 2", artist="Artist 2",
            genre="Pop", mbid=None, last_modified=0.0, duration=200
        )
        
        self.playlist = Playlist(
            songs=[self.song1, self.song2],
            seed_songs=[self.song1]
        )

    def test_export_m3u(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_m3u(self.playlist, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("#EXTM3U", content)
            self.assertIn("Artist 1 - Song 1", content)
            self.assertIn("Artist 2 - Song 2", content)
            self.assertIn("/music/song1.mp3", content)
            self.assertIn("/music/song2.mp3", content)
            self.assertIn("#EXTINF:180", content)
            self.assertIn("#EXTINF:200", content)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_m3u_with_none_duration(self):
        song_no_duration = Song(
            id=3, file_path="/music/song3.mp3", title="Song 3", artist="Artist 3",
            genre="Rock", mbid=None, last_modified=0.0, duration=None
        )
        playlist = Playlist(songs=[song_no_duration])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_m3u(playlist, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("#EXTINF:-1", content)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_m3u8(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u8', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_m3u8(self.playlist, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("#EXTM3U", content)
            self.assertIn("Artist 1 - Song 1", content)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_json(self.playlist, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn("created_at", data)
            self.assertIn("seed_songs", data)
            self.assertIn("songs", data)
            self.assertEqual(len(data["songs"]), 2)
            self.assertEqual(len(data["seed_songs"]), 1)
            self.assertEqual(data["songs"][0]["title"], "Song 1")
            self.assertEqual(data["songs"][0]["artist"], "Artist 1")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_with_format_m3u(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export(self.playlist, temp_path, format="m3u")
            
            self.assertTrue(Path(temp_path).exists())
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_with_format_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export(self.playlist, temp_path, format="json")
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("songs", data)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_export_unsupported_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(ValueError):
                self.exporter.export(self.playlist, temp_path, format="txt")
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
