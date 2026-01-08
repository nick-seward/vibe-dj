import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { SearchForm } from './components/SearchForm'
import { SearchResults } from './components/SearchResults'
import { PlaylistView } from './components/PlaylistView'
import { ChoiceListDrawer } from './components/ChoiceListDrawer'
import { ChoiceListProvider, useChoiceList } from './context/ChoiceListContext'
import { useSearchSongs, useGeneratePlaylist, useSyncToNavidrome } from './hooks/useApi'
import type { AppScreen, Song, PlaylistResponse, SearchParams } from './types'

function AppContent() {
  const [screen, setScreen] = useState<AppScreen>('search')
  const [searchResults, setSearchResults] = useState<Song[]>([])
  const [playlist, setPlaylist] = useState<PlaylistResponse | null>(null)

  const { songs: choiceListSongs, clearAll } = useChoiceList()
  const { search, loading: searching } = useSearchSongs()
  const { generate, loading: generating } = useGeneratePlaylist()
  const { sync } = useSyncToNavidrome()

  const handleSearch = async (params: SearchParams) => {
    try {
      const results = await search(params)
      setSearchResults(results)
      setScreen('results')
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
    setSearchResults([])
    setPlaylist(null)
    clearAll()
  }

  const handleBackToSearch = () => {
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
              <SearchForm onSearch={handleSearch} loading={searching} />
            </motion.div>
          )}

          {screen === 'results' && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <SearchResults
                results={searchResults}
                onBack={handleBackToSearch}
                onGeneratePlaylist={handleGeneratePlaylist}
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
        </AnimatePresence>
      </div>

      <ChoiceListDrawer />
    </div>
  )
}

function App() {
  return (
    <ChoiceListProvider>
      <AppContent />
    </ChoiceListProvider>
  )
}

export default App
