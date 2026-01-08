import { useState, type FormEvent } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import type { SearchParams } from '@/types'

interface SearchFormProps {
  onSearch: (params: SearchParams) => Promise<void>
  loading: boolean
}

export function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [artist, setArtist] = useState('')
  const [title, setTitle] = useState('')
  const [album, setAlbum] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!artist.trim() && !title.trim() && !album.trim()) {
      setError('Please enter at least one search field')
      return
    }

    const params: SearchParams = {}
    if (artist.trim()) params.artist = artist.trim()
    if (title.trim()) params.title = title.trim()
    if (album.trim()) params.album = album.trim()

    await onSearch(params)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-xl mx-auto"
    >
      <div className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-4">
          Vibe DJ
        </h1>
        <p className="text-text-muted text-lg">
          Find songs to build your perfect vibe
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="artist" className="block text-sm font-medium text-text-muted mb-2">
            Artist
          </label>
          <input
            type="text"
            id="artist"
            value={artist}
            onChange={(e) => setArtist(e.target.value)}
            placeholder="Enter artist name..."
            className="input-field"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="title" className="block text-sm font-medium text-text-muted mb-2">
            Song Title
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter song title..."
            className="input-field"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="album" className="block text-sm font-medium text-text-muted mb-2">
            Album
          </label>
          <input
            type="text"
            id="album"
            value={album}
            onChange={(e) => setAlbum(e.target.value)}
            placeholder="Enter album name..."
            className="input-field"
            disabled={loading}
          />
        </div>

        {error && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-400 text-sm text-center"
          >
            {error}
          </motion.p>
        )}

        <motion.button
          type="submit"
          disabled={loading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Search Songs
            </>
          )}
        </motion.button>
      </form>
    </motion.div>
  )
}
