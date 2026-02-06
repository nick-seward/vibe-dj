import { ArrowLeft, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { SongCard } from './SongCard'
import { useChoiceList } from '@/context/ChoiceListContext'
import type { Song, PageSize, PaginatedSearchResult } from '@/types'
import { PAGE_SIZE_OPTIONS, MAX_SEARCH_DEPTH } from '@/types'

interface SearchResultsProps {
  results: PaginatedSearchResult
  pageSize: PageSize
  onPageSizeChange: (size: PageSize) => void
  onPageChange: (offset: number) => void
  onBack: () => void
  onGeneratePlaylist: () => void
  loading?: boolean
}

function PaginationControls({
  currentPage,
  totalPages,
  canGoPrevious,
  canGoNext,
  onPrevious,
  onNext,
  loading,
}: {
  currentPage: number
  totalPages: number
  canGoPrevious: boolean
  canGoNext: boolean
  onPrevious: () => void
  onNext: () => void
  loading: boolean
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center justify-center gap-4"
    >
      <button
        onClick={onPrevious}
        disabled={!canGoPrevious || loading}
        className="flex items-center gap-1 px-4 py-2 rounded-lg bg-surface hover:bg-surface-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="w-5 h-5" />
        Previous
      </button>

      <span className="text-text-muted">
        Page {currentPage} of {totalPages}
      </span>

      <button
        onClick={onNext}
        disabled={!canGoNext || loading}
        className="flex items-center gap-1 px-4 py-2 rounded-lg bg-surface hover:bg-surface-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Next
        <ChevronRight className="w-5 h-5" />
      </button>
    </motion.div>
  )
}

export function SearchResults({ 
  results, 
  pageSize, 
  onPageSizeChange, 
  onPageChange, 
  onBack, 
  onGeneratePlaylist,
  loading = false,
}: SearchResultsProps) {
  const { songs: choiceList, addSong, isFull, hasSong } = useChoiceList()

  const handleAddSong = (song: Song) => {
    addSong(song)
  }

  const currentPage = Math.floor(results.offset / pageSize) + 1
  const totalPages = Math.ceil(Math.min(results.total, MAX_SEARCH_DEPTH) / pageSize)
  const canGoPrevious = results.offset > 0
  const canGoNext = results.offset + pageSize < results.total && results.offset + pageSize < MAX_SEARCH_DEPTH

  const handlePrevious = () => {
    if (canGoPrevious) {
      onPageChange(Math.max(0, results.offset - pageSize))
    }
  }

  const handleNext = () => {
    if (canGoNext) {
      onPageChange(results.offset + pageSize)
    }
  }

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onPageSizeChange(Number(e.target.value) as PageSize)
  }

  const displayedTotal = Math.min(results.total, MAX_SEARCH_DEPTH)
  const startResult = results.offset + 1
  const endResult = Math.min(results.offset + results.songs.length, displayedTotal)

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

      {results.songs.length === 0 ? (
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <p className="text-text-muted">
              Showing {startResult}-{endResult} of {displayedTotal} song{displayedTotal !== 1 ? 's' : ''}
              {results.total > MAX_SEARCH_DEPTH && (
                <span className="text-text-muted/70"> (limited to {MAX_SEARCH_DEPTH})</span>
              )}
              {isFull && (
                <span className="ml-2 text-secondary">
                  (Choice list full - remove a song to add more)
                </span>
              )}
            </p>

            <div className="flex items-center gap-2">
              <label htmlFor="pageSize" className="text-sm text-text-muted">
                Results per page:
              </label>
              <select
                id="pageSize"
                value={pageSize}
                onChange={handlePageSizeChange}
                disabled={loading}
                className="bg-surface border border-surface-light rounded-lg px-3 py-1.5 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="mb-4">
              <PaginationControls
                currentPage={currentPage}
                totalPages={totalPages}
                canGoPrevious={canGoPrevious}
                canGoNext={canGoNext}
                onPrevious={handlePrevious}
                onNext={handleNext}
                loading={loading}
              />
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {results.songs.map((song) => (
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

          {totalPages > 1 && (
            <div className="mt-8">
              <PaginationControls
                currentPage={currentPage}
                totalPages={totalPages}
                canGoPrevious={canGoPrevious}
                canGoNext={canGoNext}
                onPrevious={handlePrevious}
                onNext={handleNext}
                loading={loading}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
