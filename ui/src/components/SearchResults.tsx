import { ArrowLeft, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { SongCard } from './SongCard'
import { useChoiceList } from '@/context/ChoiceListContext'
import type { Song } from '@/types'

interface SearchResultsProps {
  results: Song[]
  onBack: () => void
  onGeneratePlaylist: () => void
}

export function SearchResults({ results, onBack, onGeneratePlaylist }: SearchResultsProps) {
  const { songs: choiceList, addSong, isFull, hasSong } = useChoiceList()

  const handleAddSong = (song: Song) => {
    addSong(song)
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-text-muted hover:text-text transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Search
        </button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onGeneratePlaylist}
          disabled={choiceList.length === 0}
          className="btn-primary flex items-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          Generate Playlist ({choiceList.length}/3)
        </motion.button>
      </motion.div>

      {results.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <p className="text-text-muted text-lg">No songs found</p>
          <p className="text-text-muted/70 mt-2">Try adjusting your search terms</p>
        </motion.div>
      ) : (
        <>
          <p className="text-text-muted mb-4">
            Found {results.length} song{results.length !== 1 ? 's' : ''}
            {isFull && (
              <span className="ml-2 text-secondary">
                (Choice list full - remove a song to add more)
              </span>
            )}
          </p>

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {results.map((song) => (
                <SongCard
                  key={song.id}
                  song={song}
                  isSelected={hasSong(song.id)}
                  onAdd={() => handleAddSong(song)}
                  disabled={isFull && !hasSong(song.id)}
                />
              ))}
            </AnimatePresence>
          </div>
        </>
      )}
    </div>
  )
}
