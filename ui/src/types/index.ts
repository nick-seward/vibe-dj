export interface Song {
  id: number
  file_path: string
  title: string
  artist: string
  album: string
  genre: string
  duration: number | null
  last_modified: number
}

export interface SearchParams {
  artist?: string
  title?: string
  album?: string
}

export interface SongsListResponse {
  songs: Song[]
  total: number
  limit: number
  offset: number
}

export interface NavidromeConfig {
  url?: string
  username?: string
  password?: string
  playlist_name?: string
}

export interface PlaylistRequest {
  seeds: SeedSong[]
  length: number
  bpm_jitter: number
  format: 'json' | 'm3u' | 'm3u8'
  sync_to_navidrome: boolean
  navidrome_config?: NavidromeConfig
}

export interface SeedSong {
  title: string
  artist: string
  album: string
}

export interface PlaylistResponse {
  songs: Song[]
  seed_songs: Song[]
  created_at: string
  length: number
}

export type AppScreen = 'search' | 'results' | 'playlist'
