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
  limit?: number
  offset?: number
}

export interface PaginatedSearchResult {
  songs: Song[]
  total: number
  limit: number
  offset: number
}

export const PAGE_SIZE_OPTIONS = [50, 100, 150, 200] as const
export type PageSize = typeof PAGE_SIZE_OPTIONS[number]
export const DEFAULT_PAGE_SIZE: PageSize = 50
export const MAX_SEARCH_DEPTH = 1000

export interface SongsListResponse {
  songs: Song[]
  total: number
  limit: number
  offset: number
}

export const PLAYLIST_SIZE_OPTIONS = [15, 20, 25, 30, 35, 40] as const
export type PlaylistSize = typeof PLAYLIST_SIZE_OPTIONS[number]
export const DEFAULT_PLAYLIST_SIZE: PlaylistSize = 20

export const BPM_JITTER_MIN = 1.0
export const BPM_JITTER_MAX = 20.0
export const DEFAULT_BPM_JITTER = 5.0

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

export type AppScreen = 'search' | 'results' | 'playlist' | 'config'

export interface ConfigResponse {
  music_library: string
  navidrome_url: string | null
  navidrome_username: string | null
  has_navidrome_password: boolean
  default_playlist_size: number
  default_bpm_jitter: number
}

export interface ValidatePathResponse {
  valid: boolean
  exists: boolean
  is_directory: boolean
  message: string
}

export interface IndexJobResponse {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: {
    phase?: string
    message?: string
    processed?: number
    total?: number
  } | null
  error: string | null
  started_at: string | null
  completed_at: string | null
}

export interface ActiveJobResponse {
  job_id: string | null
  status: 'queued' | 'running' | 'idle'
  progress: {
    phase?: string
    message?: string
    processed?: number
    total?: number
  } | null
  error: string | null
  started_at: string | null
  completed_at: string | null
}

export interface LibraryStats {
  total_songs: number
  artist_count: number
  album_count: number
  total_duration: number
  songs_with_features: number
  last_indexed: number | null
}

export interface TestNavidromeResponse {
  success: boolean
  message: string
}

export interface UpdateConfigRequest {
  music_library?: string
  navidrome_url?: string
  navidrome_username?: string
  navidrome_password?: string
  default_playlist_size?: number
  default_bpm_jitter?: number
}

export interface UpdateConfigResponse {
  success: boolean
  message: string
}
