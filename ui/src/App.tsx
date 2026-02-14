import { useState, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { SearchForm } from './components/SearchForm'
import { SearchResults } from './components/SearchResults'
import { PlaylistView } from './components/PlaylistView'
import { ChoiceListDrawer } from './components/ChoiceListDrawer'
import { ConfigScreen } from './components/ConfigScreen'
import { ChoiceListProvider, useChoiceList } from './context/ChoiceListContext'
import { ToastProvider } from './context/ToastContext'
import { useSearchSongs, useGeneratePlaylist, useSyncToNavidrome } from './hooks/useApi'
import { useConfig } from './hooks/useConfig'
import type {
  AppScreen,
  PlaylistResponse,
  SearchParams,
  PaginatedSearchResult,
  PageSize,
  PlaylistSize,
} from './types'
import { DEFAULT_PAGE_SIZE, DEFAULT_PLAYLIST_SIZE, DEFAULT_BPM_JITTER, BPM_JITTER_MIN, BPM_JITTER_MAX, PLAYLIST_SIZE_OPTIONS } from './types'

function AppContent() {
  const [screen, setScreen] = useState<AppScreen>('search')
  const [searchResults, setSearchResults] = useState<PaginatedSearchResult | null>(null)
  const [playlist, setPlaylist] = useState<PlaylistResponse | null>(null)
  const [pageSize, setPageSize] = useState<PageSize>(DEFAULT_PAGE_SIZE)
  const [playlistSizeOverride, setPlaylistSizeOverride] = useState<PlaylistSize | null>(null)
  const currentSearchParams = useRef<SearchParams>({})

  const { songs: choiceListSongs, clearAll } = useChoiceList()
  const { search, loading: searching } = useSearchSongs()
  const { generate, loading: generating } = useGeneratePlaylist()
  const { sync } = useSyncToNavidrome()
  const { config } = useConfig()

  const configuredPlaylistSize =
    config && PLAYLIST_SIZE_OPTIONS.includes(config.default_playlist_size as PlaylistSize)
      ? (config.default_playlist_size as PlaylistSize)
      : DEFAULT_PLAYLIST_SIZE

  const configuredBpmJitter =
    config && config.default_bpm_jitter >= BPM_JITTER_MIN && config.default_bpm_jitter <= BPM_JITTER_MAX
      ? config.default_bpm_jitter
      : DEFAULT_BPM_JITTER

  const selectedPlaylistSize = playlistSizeOverride ?? configuredPlaylistSize

  const handleSearch = async (params: SearchParams) => {
    try {
      currentSearchParams.current = params
      const results = await search({ ...params, limit: pageSize, offset: 0 })
      setSearchResults(results)
      setScreen('results')
    } catch {
      // Error is handled in the hook
    }
  }

  const handlePageChange = async (offset: number) => {
    try {
      const results = await search({ ...currentSearchParams.current, limit: pageSize, offset })
      setSearchResults(results)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // Error is handled in the hook
    }
  }

  const handlePageSizeChange = async (newPageSize: PageSize) => {
    setPageSize(newPageSize)
    try {
      const results = await search({ ...currentSearchParams.current, limit: newPageSize, offset: 0 })
      setSearchResults(results)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // Error is handled in the hook
    }
  }

  const handleGeneratePlaylist = async (length: number) => {
    if (choiceListSongs.length === 0) return

    try {
      const result = await generate(choiceListSongs, length, configuredBpmJitter)
      setPlaylist(result)
      setScreen('playlist')
    } catch {
      // Error is handled in the hook
    }
  }

  const handleRegenerate = async () => {
    if (choiceListSongs.length === 0) return

    try {
      const result = await generate(choiceListSongs, selectedPlaylistSize, configuredBpmJitter)
      setPlaylist(result)
    } catch {
      // Error is handled in the hook
    }
  }

  const handlePlaylistSizeChange = (newPlaylistSize: PlaylistSize) => {
    setPlaylistSizeOverride(newPlaylistSize)
  }

  const handleSyncToNavidrome = async (
    playlistName: string,
  ): Promise<boolean> => {
    if (!playlist) return false
    return await sync(playlist.songs, playlistName)
  }

  const handleStartOver = () => {
    setScreen('search')
    setSearchResults(null)
    setPlaylist(null)
    clearAll()
  }

  const handleBackToSearch = () => {
    setScreen('search')
  }

  const handleOpenConfig = () => {
    setScreen('config')
  }

  const handleCloseConfig = () => {
    setScreen('search')
  }

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-8 md:py-16">
        <AnimatePresence mode="wait">
          {screen === 'search' && (
            <motion.div
              key="search"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <SearchForm onSearch={handleSearch} loading={searching} onSettingsClick={handleOpenConfig} />
            </motion.div>
          )}

          {screen === 'results' && searchResults && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <SearchResults
                results={searchResults}
                pageSize={pageSize}
                selectedPlaylistSize={selectedPlaylistSize}
                onPageSizeChange={handlePageSizeChange}
                onPlaylistSizeChange={handlePlaylistSizeChange}
                onPageChange={handlePageChange}
                onBack={handleBackToSearch}
                onGeneratePlaylist={handleGeneratePlaylist}
                loading={searching}
              />
            </motion.div>
          )}

          {screen === 'playlist' && playlist && (
            <motion.div
              key="playlist"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <PlaylistView
                playlist={playlist}
                onRegenerate={handleRegenerate}
                onSyncToNavidrome={handleSyncToNavidrome}
                onStartOver={handleStartOver}
                regenerating={generating}
              />
            </motion.div>
          )}

          {screen === 'config' && (
            <motion.div
              key="config"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <ConfigScreen onClose={handleCloseConfig} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <ChoiceListDrawer />
    </div>
  )
}

function App() {
  return (
    <ToastProvider>
      <ChoiceListProvider>
        <AppContent />
      </ChoiceListProvider>
    </ToastProvider>
  )
}

export default App
