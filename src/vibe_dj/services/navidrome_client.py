import hashlib
import random
import string
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from loguru import logger


class NavidromeClient:
    """
    Client for interacting with Navidrome server using the Subsonic API.
    
    Supports song search, playlist creation, and playlist updates with
    retry logic and comprehensive error handling.
    """
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        client_id: str = "vibe-dj",
        api_version: str = "1.16.1"
    ):
        """
        Initialize Navidrome client.
        
        Args:
            base_url: Base URL of Navidrome server (e.g., http://192.168.1.100:4533)
            username: Navidrome username
            password: Navidrome password
            client_id: Client identifier for API requests
            api_version: Subsonic API version to use
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.client_id = client_id
        self.api_version = api_version
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{client_id}/1.0'
        })
    
    def _generate_auth_token(self) -> tuple[str, str]:
        """
        Generate authentication token and salt for Subsonic API.
        
        Returns:
            Tuple of (token, salt) where token is MD5(password + salt)
        """
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        token = hashlib.md5(f"{self.password}{salt}".encode()).hexdigest()
        return token, salt
    
    def _call(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make an API call to Navidrome with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., 'search3', 'createPlaylist')
            params: Query parameters for the request
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response from the API
            
        Raises:
            requests.exceptions.RequestException: On network/HTTP errors
            ValueError: On API errors or invalid responses
        """
        if params is None:
            params = {}
        
        token, salt = self._generate_auth_token()
        params.update({
            'u': self.username,
            't': token,
            's': salt,
            'v': self.api_version,
            'c': self.client_id,
            'f': 'json'
        })
        
        url = urljoin(f"{self.base_url}/rest/", endpoint)
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if 'subsonic-response' not in data:
                    raise ValueError(f"Invalid API response: missing 'subsonic-response' key")
                
                subsonic_response = data['subsonic-response']
                
                if subsonic_response.get('status') == 'failed':
                    error = subsonic_response.get('error', {})
                    error_msg = error.get('message', 'Unknown error')
                    error_code = error.get('code', 0)
                    raise ValueError(f"API error {error_code}: {error_msg}")
                
                return subsonic_response
                
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request timeout after {max_retries} attempts")
                    raise
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
        
        raise RuntimeError("Unexpected error in _call method")
    
    def search_song(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> Optional[str]:
        """
        Search for a song on Navidrome with fallback strategy.
        
        Uses a three-tier search strategy:
        1. Search by title + artist + album (most accurate)
        2. Fallback to title + artist
        3. Fallback to title only
        
        Args:
            title: Song title
            artist: Artist name
            album: Album name (optional but recommended)
            
        Returns:
            Song ID if found, None otherwise
        """
        search_strategies = []
        
        if album:
            search_strategies.append(('title + artist + album', f"{title} {artist} {album}"))
        
        search_strategies.append(('title + artist', f"{title} {artist}"))
        search_strategies.append(('title only', title))
        
        for strategy_name, query in search_strategies:
            try:
                response = self._call('search3', {'query': query})
                
                search_result = response.get('searchResult3', {})
                songs = search_result.get('song', [])
                
                if songs:
                    song_id = songs[0].get('id')
                    if song_id:
                        logger.debug(f"Found song '{title}' using {strategy_name}: ID={song_id}")
                        return song_id
                        
            except Exception as e:
                logger.warning(f"Search failed for '{title}' using {strategy_name}: {e}")
                continue
        
        logger.warning(f"Could not find song '{title}' by {artist} on Navidrome")
        return None
    
    def get_playlists(self) -> List[Dict[str, Any]]:
        """
        Get all playlists from Navidrome.
        
        Returns:
            List of playlist dictionaries with id, name, songCount, etc.
        """
        try:
            response = self._call('getPlaylists')
            playlists_data = response.get('playlists', {})
            playlists = playlists_data.get('playlist', [])
            
            if isinstance(playlists, dict):
                playlists = [playlists]
            
            return playlists
            
        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            raise
    
    def get_playlist_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a playlist by name.
        
        Args:
            name: Playlist name to search for
            
        Returns:
            Playlist dictionary if found, None otherwise
        """
        try:
            playlists = self.get_playlists()
            
            for playlist in playlists:
                if playlist.get('name') == name:
                    return playlist
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to search for playlist '{name}': {e}")
            return None
    
    def create_playlist(self, name: str, song_ids: List[str]) -> Optional[str]:
        """
        Create a new playlist on Navidrome.
        
        Args:
            name: Playlist name
            song_ids: List of song IDs to add to the playlist
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        if not song_ids:
            logger.warning("Cannot create playlist with no songs")
            return None
        
        try:
            params = {
                'name': name,
                'songId': song_ids
            }
            
            response = self._call('createPlaylist', params)
            
            playlist = response.get('playlist', {})
            playlist_id = playlist.get('id')
            
            if playlist_id:
                logger.info(f"Created playlist '{name}' with {len(song_ids)} songs (ID: {playlist_id})")
                return playlist_id
            else:
                logger.error(f"Failed to create playlist '{name}': no ID returned")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create playlist '{name}': {e}")
            return None
    
    def update_playlist(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        song_ids_to_add: Optional[List[str]] = None,
        song_indices_to_remove: Optional[List[int]] = None
    ) -> bool:
        """
        Update an existing playlist on Navidrome.
        
        Args:
            playlist_id: ID of the playlist to update
            name: New name for the playlist (optional)
            song_ids_to_add: List of song IDs to add (optional)
            song_indices_to_remove: List of song indices to remove (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            params = {'playlistId': playlist_id}
            
            if name:
                params['name'] = name
            
            if song_ids_to_add:
                params['songIdToAdd'] = song_ids_to_add
            
            if song_indices_to_remove:
                params['songIndexToRemove'] = song_indices_to_remove
            
            self._call('updatePlaylist', params)
            
            logger.info(f"Updated playlist ID {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update playlist {playlist_id}: {e}")
            return False
    
    def replace_playlist_songs(self, playlist_id: str, song_ids: List[str]) -> bool:
        """
        Replace all songs in a playlist with a new set.
        
        This is done by removing all existing songs and adding new ones.
        
        Args:
            playlist_id: ID of the playlist to update
            song_ids: New list of song IDs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self._call('getPlaylist', {'id': playlist_id})
            playlist = response.get('playlist', {})
            entries = playlist.get('entry', [])
            
            if isinstance(entries, dict):
                entries = [entries]
            
            existing_count = len(entries)
            
            if existing_count > 0:
                indices_to_remove = list(range(existing_count))
                if not self.update_playlist(playlist_id, song_indices_to_remove=indices_to_remove):
                    return False
            
            if song_ids:
                return self.update_playlist(playlist_id, song_ids_to_add=song_ids)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to replace playlist songs: {e}")
            return False
