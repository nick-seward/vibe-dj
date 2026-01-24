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
import type { AppScreen, PlaylistResponse, SearchParams, PaginatedSearchResult, PageSize } from './types'
import { DEFAULT_PAGE_SIZE } from './types'

function AppContent() {
  const [screen, setScreen] = useState<AppScreen>('search')
  const [searchResults, setSearchResults] = useState<PaginatedSearchResult | null>(null)
  const [playlist, setPlaylist] = useState<PlaylistResponse | null>(null)
  const [pageSize, setPageSize] = useState<PageSize>(DEFAULT_PAGE_SIZE)
  const currentSearchParams = useRef<SearchParams>({})

  const { songs: choiceListSongs, clearAll } = useChoiceList()
  const { search, loading: searching } = useSearchSongs()
  const { generate, loading: generating } = useGeneratePlaylist()
  const { sync } = useSyncToNavidrome()

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

  const handleGeneratePlaylist = async () => {
    if (choiceListSongs.length === 0) return

    try {
      const result = await generate(choiceListSongs)
      setPlaylist(result)
      setScreen('playlist')
    } catch {
      // Error is handled in the hook
    }
  }

  const handleRegenerate = async () => {
    if (choiceListSongs.length === 0) return

    try {
      const result = await generate(choiceListSongs)
      setPlaylist(result)
    } catch {
      // Error is handled in the hook
    }
  }

  const handleSyncToNavidrome = async (
    playlistName: string,
    credentials?: { url?: string; username?: string; password?: string }
  ): Promise<boolean> => {
    if (!playlist) return false
    return await sync(playlist.songs, playlistName, credentials)
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
                onPageSizeChange={handlePageSizeChange}
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
