import { useState, useCallback } from 'react'
import { Loader2, CheckCircle, Save, ListMusic } from 'lucide-react'
import { motion } from 'framer-motion'
import { useSaveConfig } from '@/hooks/useConfig'
import { useToast } from '@/context/ToastContext'
import {
  PLAYLIST_SIZE_OPTIONS,
  BPM_JITTER_MIN,
  BPM_JITTER_MAX,
} from '@/types'

interface PlaylistTabProps {
  defaultPlaylistSize: number
  defaultBpmJitter: number
  originalPlaylistSize: number
  originalBpmJitter: number
  onPlaylistSizeChange: (value: number) => void
  onBpmJitterChange: (value: number) => void
  onSaveSuccess: () => void
}

export function PlaylistTab({
  defaultPlaylistSize,
  defaultBpmJitter,
  originalPlaylistSize,
  originalBpmJitter,
  onPlaylistSizeChange,
  onBpmJitterChange,
  onSaveSuccess,
}: PlaylistTabProps) {
  const [showSaveSuccess, setShowSaveSuccess] = useState(false)
  const { saving, saveConfig } = useSaveConfig()
  const { showToast } = useToast()

  const hasSizeChange = defaultPlaylistSize !== originalPlaylistSize
  const hasJitterChange = defaultBpmJitter !== originalBpmJitter
  const hasChanges = hasSizeChange || hasJitterChange

  const isSaveDisabled = !hasChanges || saving

  const handleSave = useCallback(async () => {
    if (isSaveDisabled) return

    const updates: { default_playlist_size?: number; default_bpm_jitter?: number } = {}

    if (hasSizeChange) {
      updates.default_playlist_size = defaultPlaylistSize
    }
    if (hasJitterChange) {
      updates.default_bpm_jitter = defaultBpmJitter
    }

    const result = await saveConfig(updates)

    if (result.success) {
      showToast('success', result.message)
      setShowSaveSuccess(true)

      setTimeout(() => {
        setShowSaveSuccess(false)
        onSaveSuccess()
      }, 2000)
    } else {
      showToast('error', result.message)
    }
  }, [isSaveDisabled, hasSizeChange, hasJitterChange, defaultPlaylistSize, defaultBpmJitter, saveConfig, showToast, onSaveSuccess])

  // Visual oscillation indicator: higher jitter = more movement
  const oscillationIntensity = (defaultBpmJitter - BPM_JITTER_MIN) / (BPM_JITTER_MAX - BPM_JITTER_MIN)

  return (
    <div className="space-y-6">
      {/* Header with Save Button */}
      <div className="flex justify-end">
        <motion.button
          onClick={handleSave}
          disabled={isSaveDisabled && !showSaveSuccess}
          whileHover={!isSaveDisabled ? { scale: 1.02 } : {}}
          whileTap={!isSaveDisabled ? { scale: 0.98 } : {}}
          className={`flex items-center gap-2 font-medium px-4 py-2 rounded-lg transition-all duration-200 ${
            showSaveSuccess
              ? 'bg-success text-white cursor-default'
              : 'btn-primary'
          }`}
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : showSaveSuccess ? (
            <>
              <CheckCircle className="w-4 h-4" />
              Saved
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save
            </>
          )}
        </motion.button>
      </div>

      {/* Default Playlist Size */}
      <div>
        <label htmlFor="playlistSize" className="block text-sm font-medium text-text-muted mb-2">
          Default Playlist Size
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <ListMusic className="w-5 h-5" />
          </div>
          <select
            id="playlistSize"
            value={defaultPlaylistSize}
            onChange={(e) => onPlaylistSizeChange(Number(e.target.value))}
            className="input-field !pl-14 appearance-none cursor-pointer"
          >
            {PLAYLIST_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size} songs
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        <p className="text-xs text-text-muted mt-1.5">
          Number of songs generated per playlist
        </p>
      </div>

      {/* BPM Jitter Slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="bpmJitter" className="block text-sm font-medium text-text-muted">
            BPM Jitter
          </label>
          <span className="text-sm font-mono text-text">
            {defaultBpmJitter.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          id="bpmJitter"
          min={BPM_JITTER_MIN}
          max={BPM_JITTER_MAX}
          step={0.5}
          value={defaultBpmJitter}
          onChange={(e) => onBpmJitterChange(Number(e.target.value))}
          className="w-full h-2 bg-surface-hover rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary
            [&::-webkit-slider-thumb]:hover:bg-primary-hover [&::-webkit-slider-thumb]:transition-colors
            [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-0
            [&::-moz-range-thumb]:hover:bg-primary-hover [&::-moz-range-thumb]:transition-colors"
        />
        <div className="flex justify-between text-xs text-text-muted mt-1">
          <span>Tight ({BPM_JITTER_MIN})</span>
          <span>Loose ({BPM_JITTER_MAX})</span>
        </div>
        <p className="text-xs text-text-muted mt-1.5">
          Controls how much BPM variation is allowed when ordering playlist songs
        </p>
      </div>

      {/* Visual Oscillation Indicator */}
      <div className="bg-surface-hover rounded-lg p-4 border border-border">
        <div className="flex items-center gap-2 text-text-muted mb-3">
          <span className="text-sm font-medium">BPM Variation Preview</span>
        </div>
        <div className="flex items-center justify-center gap-1 h-12">
          {Array.from({ length: 15 }).map((_, i) => {
            const center = 7
            const distFromCenter = Math.abs(i - center)
            const maxHeight = 8 + oscillationIntensity * 40
            const height = maxHeight - (distFromCenter * (maxHeight - 8)) / center
            return (
              <motion.div
                key={i}
                className="w-1.5 rounded-full bg-primary"
                animate={{
                  height: [height * 0.6, height, height * 0.6],
                }}
                transition={{
                  duration: 0.8 + (1 - oscillationIntensity) * 1.2,
                  repeat: Infinity,
                  delay: i * 0.05,
                  ease: 'easeInOut',
                }}
              />
            )
          })}
        </div>
        <p className="text-xs text-text-muted text-center mt-2">
          {oscillationIntensity < 0.3
            ? 'Songs will stay close to the target BPM'
            : oscillationIntensity < 0.7
              ? 'Moderate BPM variation between songs'
              : 'Wide BPM swings for eclectic playlists'}
        </p>
      </div>
    </div>
  )
}
