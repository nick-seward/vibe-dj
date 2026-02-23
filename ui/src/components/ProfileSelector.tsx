import { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronDown, User, Plus, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useProfileContext } from '@/context/ProfileContext'
import type { CreateProfileRequest } from '@/types'

interface AddProfileModalProps {
  onClose: () => void
  onAdd: (request: CreateProfileRequest) => Promise<void>
}

function AddProfileModal({ onClose, onAdd }: AddProfileModalProps) {
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = displayName.trim()
    if (!trimmed) {
      setError('Display name is required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await onAdd({ display_name: trimmed })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile')
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className="bg-surface border border-border rounded-xl p-6 w-full max-w-sm mx-4 shadow-xl"
      >
        <h2 className="text-lg font-semibold text-text mb-4">Add New Profile</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="profileDisplayName" className="block text-sm font-medium text-text-muted mb-2">
              Display Name
            </label>
            <input
              type="text"
              id="profileDisplayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Nick, Family"
              className="input-field"
              autoFocus
              disabled={saving}
            />
          </div>
          {error && (
            <p className="text-error text-sm">{error}</p>
          )}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-text-muted hover:text-text hover:bg-surface-hover rounded-lg transition-all duration-200"
              disabled={saving}
            >
              Cancel
            </button>
            <motion.button
              type="submit"
              disabled={saving}
              whileHover={!saving ? { scale: 1.02 } : {}}
              whileTap={!saving ? { scale: 0.98 } : {}}
              className="btn-primary px-4 py-2 text-sm"
            >
              {saving ? 'Adding...' : 'Add Profile'}
            </motion.button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

export function ProfileSelector() {
  const { profiles, activeProfile, activeProfileId, setActiveProfileId, createProfile, refreshProfiles } = useProfileContext()
  const [open, setOpen] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
      setOpen(false)
    }
  }, [])

  useEffect(() => {
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open, handleClickOutside])

  const handleSelect = (id: number) => {
    setActiveProfileId(id)
    setOpen(false)
  }

  const handleAddProfile = async (request: CreateProfileRequest) => {
    const newProfile = await createProfile(request)
    await refreshProfiles()
    setActiveProfileId(newProfile.id)
  }

  const displayLabel = activeProfile?.display_name ?? 'Select Profile'

  return (
    <>
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setOpen((prev) => !prev)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-text-muted hover:text-text hover:bg-surface-hover rounded-lg transition-all duration-200"
          aria-label="Select active profile"
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          <User className="w-4 h-4 shrink-0" />
          <span className="max-w-[120px] truncate">{displayLabel}</span>
          <ChevronDown className={`w-4 h-4 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.12 }}
              className="absolute right-0 mt-1 w-48 bg-surface border border-border rounded-xl shadow-xl z-40 overflow-hidden"
              role="listbox"
              aria-label="Profile list"
            >
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  role="option"
                  aria-selected={profile.id === activeProfileId}
                  onClick={() => handleSelect(profile.id)}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left hover:bg-surface-hover transition-colors duration-150"
                >
                  <span className="flex-1 truncate text-text">{profile.display_name}</span>
                  {profile.id === activeProfileId && (
                    <Check className="w-4 h-4 text-primary shrink-0" />
                  )}
                </button>
              ))}

              <div className="border-t border-border">
                <button
                  onClick={() => { setOpen(false); setShowAddModal(true) }}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors duration-150"
                >
                  <Plus className="w-4 h-4 shrink-0" />
                  <span>Add New Profile</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {showAddModal && (
          <AddProfileModal
            onClose={() => setShowAddModal(false)}
            onAdd={handleAddProfile}
          />
        )}
      </AnimatePresence>
    </>
  )
}
