import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { Song } from '@/types'

const MAX_SONGS = 3

interface ChoiceListContextType {
  songs: Song[]
  addSong: (song: Song) => boolean
  removeSong: (songId: number) => void
  clearAll: () => void
  isFull: boolean
  hasSong: (songId: number) => boolean
}

const ChoiceListContext = createContext<ChoiceListContextType | undefined>(undefined)

export function ChoiceListProvider({ children }: { children: ReactNode }) {
  const [songs, setSongs] = useState<Song[]>([])

  const addSong = useCallback((song: Song): boolean => {
    if (songs.length >= MAX_SONGS) {
      return false
    }
    if (songs.some((s) => s.id === song.id)) {
      return false
    }
    setSongs((prev) => [...prev, song])
    return true
  }, [songs])

  const removeSong = useCallback((songId: number) => {
    setSongs((prev) => prev.filter((s) => s.id !== songId))
  }, [])

  const clearAll = useCallback(() => {
    setSongs([])
  }, [])

  const hasSong = useCallback((songId: number): boolean => {
    return songs.some((s) => s.id === songId)
  }, [songs])

  return (
    <ChoiceListContext.Provider
      value={{
        songs,
        addSong,
        removeSong,
        clearAll,
        isFull: songs.length >= MAX_SONGS,
        hasSong,
      }}
    >
      {children}
    </ChoiceListContext.Provider>
  )
}

export function useChoiceList() {
  const context = useContext(ChoiceListContext)
  if (context === undefined) {
    throw new Error('useChoiceList must be used within a ChoiceListProvider')
  }
  return context
}
