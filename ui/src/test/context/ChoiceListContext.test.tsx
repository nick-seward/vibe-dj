import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ChoiceListProvider, useChoiceList } from '@/context/ChoiceListContext'
import type { Song } from '@/types'

const createMockSong = (id: number): Song => ({
  id,
  file_path: `/music/song${id}.mp3`,
  title: `Song ${id}`,
  artist: `Artist ${id}`,
  album: `Album ${id}`,
  genre: 'Rock',
  duration: 180,
  last_modified: Date.now(),
})

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ChoiceListProvider>{children}</ChoiceListProvider>
)

describe('ChoiceListContext', () => {
  it('starts with empty song list', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })
    expect(result.current.songs).toEqual([])
    expect(result.current.isFull).toBe(false)
  })

  it('adds a song to the list', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })
    const song = createMockSong(1)

    act(() => {
      result.current.addSong(song)
    })

    expect(result.current.songs).toHaveLength(1)
    expect(result.current.songs[0].id).toBe(1)
  })

  it('prevents adding duplicate songs', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })
    const song = createMockSong(1)

    act(() => {
      result.current.addSong(song)
    })

    act(() => {
      const added = result.current.addSong(song)
      expect(added).toBe(false)
    })

    expect(result.current.songs).toHaveLength(1)
  })

  it('limits to 3 songs maximum', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })

    act(() => {
      result.current.addSong(createMockSong(1))
      result.current.addSong(createMockSong(2))
      result.current.addSong(createMockSong(3))
    })

    expect(result.current.isFull).toBe(true)

    act(() => {
      const added = result.current.addSong(createMockSong(4))
      expect(added).toBe(false)
    })

    expect(result.current.songs).toHaveLength(3)
  })

  it('removes a song from the list', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })

    act(() => {
      result.current.addSong(createMockSong(1))
      result.current.addSong(createMockSong(2))
    })

    act(() => {
      result.current.removeSong(1)
    })

    expect(result.current.songs).toHaveLength(1)
    expect(result.current.songs[0].id).toBe(2)
  })

  it('clears all songs', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })

    act(() => {
      result.current.addSong(createMockSong(1))
      result.current.addSong(createMockSong(2))
    })

    act(() => {
      result.current.clearAll()
    })

    expect(result.current.songs).toHaveLength(0)
  })

  it('hasSong returns correct values', () => {
    const { result } = renderHook(() => useChoiceList(), { wrapper })

    act(() => {
      result.current.addSong(createMockSong(1))
    })

    expect(result.current.hasSong(1)).toBe(true)
    expect(result.current.hasSong(2)).toBe(false)
  })
})
