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
