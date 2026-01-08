import { Plus, Check, X } from 'lucide-react'
import { motion } from 'framer-motion'
import type { Song } from '@/types'

interface SongCardProps {
  song: Song
  isSelected?: boolean
  onAdd?: () => void
  onRemove?: () => void
  disabled?: boolean
  showRemove?: boolean
}

export function SongCard({
  song,
  isSelected = false,
  onAdd,
  onRemove,
  disabled = false,
  showRemove = false,
}: SongCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`card flex items-center gap-4 ${isSelected ? 'border-primary bg-primary/10' : ''}`}
    >
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-text truncate">{song.title}</h3>
        <p className="text-sm text-text-muted truncate">{song.artist}</p>
        <p className="text-xs text-text-muted/70 truncate">{song.album}</p>
      </div>

      {showRemove && onRemove && (
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onRemove}
          className="p-2 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
          aria-label="Remove from choice list"
        >
          <X className="w-4 h-4" />
        </motion.button>
      )}

      {!showRemove && onAdd && (
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onAdd}
          disabled={disabled || isSelected}
          className={`p-2 rounded-full transition-colors ${
            isSelected
              ? 'bg-primary/20 text-primary cursor-default'
              : disabled
              ? 'bg-surface-hover text-text-muted cursor-not-allowed'
              : 'bg-primary/20 text-primary hover:bg-primary/30'
          }`}
          aria-label={isSelected ? 'Already in choice list' : 'Add to choice list'}
        >
          {isSelected ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
        </motion.button>
      )}
    </motion.div>
  )
}
