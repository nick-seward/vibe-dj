import { useState } from 'react'
import { ShoppingCart, ChevronUp, ChevronDown, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { SongCard } from './SongCard'
import { useChoiceList } from '@/context/ChoiceListContext'

export function ChoiceListDrawer() {
  const [isOpen, setIsOpen] = useState(false)
  const { songs, removeSong, clearAll } = useChoiceList()

  if (songs.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-16 right-0 w-80 bg-surface border border-border rounded-xl shadow-xl overflow-hidden"
          >
            <div className="p-3 border-b border-border flex items-center justify-between">
              <h3 className="font-medium text-text">Choice List ({songs.length}/3)</h3>
              <button
                onClick={clearAll}
                className="text-text-muted hover:text-red-400 transition-colors"
                aria-label="Clear all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
              {songs.map((song) => (
                <SongCard
                  key={song.id}
                  song={song}
                  showRemove
                  onRemove={() => removeSong(song.id)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="relative bg-primary hover:bg-primary-hover text-white p-4 rounded-full shadow-lg transition-colors"
      >
        <ShoppingCart className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 bg-secondary text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
          {songs.length}
        </span>
        <span className="absolute -bottom-1 -left-1 bg-surface rounded-full p-0.5">
          {isOpen ? (
            <ChevronDown className="w-3 h-3 text-text-muted" />
          ) : (
            <ChevronUp className="w-3 h-3 text-text-muted" />
          )}
        </span>
      </motion.button>
    </div>
  )
}
