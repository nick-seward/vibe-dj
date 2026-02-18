import { useState, useCallback } from 'react'
import { User, Globe, Lock, Eye, EyeOff, Pencil, Trash2, Plus, X, Loader2, CheckCircle, Save } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useProfileContext } from '@/context/ProfileContext'
import { useToast } from '@/context/ToastContext'
import type { Profile, CreateProfileRequest, UpdateProfileRequest } from '@/types'

const SHARED_PROFILE_NAME = 'Shared'

interface ProfileFormData {
  display_name: string
  subsonic_url: string
  subsonic_username: string
  subsonic_password: string
}

const emptyForm = (): ProfileFormData => ({
  display_name: '',
  subsonic_url: '',
  subsonic_username: '',
  subsonic_password: '',
})

interface ProfileFormProps {
  initial?: ProfileFormData
  isShared?: boolean
  saving: boolean
  onSave: (data: ProfileFormData) => Promise<void>
  onCancel: () => void
  hasServerPassword?: boolean
}

function ProfileForm({ initial, isShared, saving, onSave, onCancel, hasServerPassword }: ProfileFormProps) {
  const [form, setForm] = useState<ProfileFormData>(initial ?? emptyForm())
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const set = (field: keyof ProfileFormData) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.display_name.trim()) {
      setError('Display name is required')
      return
    }
    setError(null)
    try {
      await onSave(form)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="profileName" className="block text-sm font-medium text-text-muted mb-2">
          Display Name
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <User className="w-5 h-5" />
          </div>
          <input
            type="text"
            id="profileName"
            value={form.display_name}
            onChange={set('display_name')}
            placeholder="e.g. Nick, Family"
            className="input-field !pl-14"
            disabled={saving || isShared}
          />
        </div>
        {isShared && (
          <p className="text-xs text-text-muted mt-1">The Shared profile name cannot be changed.</p>
        )}
      </div>

      <div>
        <label htmlFor="profileUrl" className="block text-sm font-medium text-text-muted mb-2">
          Subsonic URL
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <Globe className="w-5 h-5" />
          </div>
          <input
            type="url"
            id="profileUrl"
            value={form.subsonic_url}
            onChange={set('subsonic_url')}
            placeholder="http://192.168.1.100:4533"
            className="input-field !pl-14"
            disabled={saving}
          />
        </div>
      </div>

      <div>
        <label htmlFor="profileUsername" className="block text-sm font-medium text-text-muted mb-2">
          Username
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <User className="w-5 h-5" />
          </div>
          <input
            type="text"
            id="profileUsername"
            value={form.subsonic_username}
            onChange={set('subsonic_username')}
            placeholder="Enter username"
            className="input-field !pl-14"
            disabled={saving}
          />
        </div>
      </div>

      <div>
        <label htmlFor="profilePassword" className="block text-sm font-medium text-text-muted mb-2">
          Password
          {hasServerPassword && !form.subsonic_password && (
            <span className="ml-2 text-xs text-text-muted/70">(configured on server)</span>
          )}
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            <Lock className="w-5 h-5" />
          </div>
          <input
            type={showPassword ? 'text' : 'password'}
            id="profilePassword"
            value={form.subsonic_password}
            onChange={set('subsonic_password')}
            placeholder={hasServerPassword ? '••••••••' : 'Enter password'}
            className="input-field !pl-14 pr-11"
            disabled={saving}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-sm">{error}</p>
      )}

      <div className="flex gap-3 justify-end pt-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-text-muted hover:text-text hover:bg-surface-hover rounded-lg transition-all duration-200"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
        <motion.button
          type="submit"
          disabled={saving}
          whileHover={!saving ? { scale: 1.02 } : {}}
          whileTap={!saving ? { scale: 0.98 } : {}}
          className="btn-primary flex items-center gap-1.5 px-4 py-2 text-sm"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save
            </>
          )}
        </motion.button>
      </div>
    </form>
  )
}

interface ProfileRowProps {
  profile: Profile
  onEdit: (profile: Profile) => void
  onDelete: (profile: Profile) => void
}

function ProfileRow({ profile, onEdit, onDelete }: ProfileRowProps) {
  const isShared = profile.display_name === SHARED_PROFILE_NAME

  return (
    <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-hover border border-border">
      <div className="flex items-center gap-3 min-w-0">
        <User className="w-5 h-5 text-text-muted shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-text truncate">{profile.display_name}</p>
          {profile.subsonic_url && (
            <p className="text-xs text-text-muted truncate">{profile.subsonic_url}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0 ml-3">
        <button
          onClick={() => onEdit(profile)}
          className="p-1.5 text-text-muted hover:text-text hover:bg-surface rounded-lg transition-all duration-150"
          aria-label={`Edit ${profile.display_name}`}
        >
          <Pencil className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDelete(profile)}
          disabled={isShared}
          className="p-1.5 text-text-muted hover:text-red-400 hover:bg-surface rounded-lg transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-text-muted disabled:hover:bg-transparent"
          aria-label={`Delete ${profile.display_name}`}
          title={isShared ? 'The Shared profile cannot be deleted' : undefined}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

type PanelMode = 'list' | 'create' | { edit: Profile }

export function ProfilesTab() {
  const { profiles, loading, createProfile, updateProfile, deleteProfile, refreshProfiles } = useProfileContext()
  const { showToast } = useToast()
  const [mode, setMode] = useState<PanelMode>('list')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<Profile | null>(null)
  const [deleting, setDeleting] = useState(false)

  const handleCreate = useCallback(async (data: ProfileFormData) => {
    setSaving(true)
    try {
      const req: CreateProfileRequest = {
        display_name: data.display_name.trim(),
        ...(data.subsonic_url.trim() && { subsonic_url: data.subsonic_url.trim() }),
        ...(data.subsonic_username.trim() && { subsonic_username: data.subsonic_username.trim() }),
        ...(data.subsonic_password && { subsonic_password: data.subsonic_password }),
      }
      await createProfile(req)
      await refreshProfiles()
      showToast('success', `Profile "${req.display_name}" created`)
      setMode('list')
    } finally {
      setSaving(false)
    }
  }, [createProfile, refreshProfiles, showToast])

  const handleUpdate = useCallback(async (profile: Profile, data: ProfileFormData) => {
    setSaving(true)
    try {
      const req: UpdateProfileRequest = {}
      if (profile.display_name !== SHARED_PROFILE_NAME) {
        req.display_name = data.display_name.trim()
      }
      if (data.subsonic_url.trim() !== (profile.subsonic_url ?? '')) {
        req.subsonic_url = data.subsonic_url.trim()
      }
      if (data.subsonic_username.trim() !== (profile.subsonic_username ?? '')) {
        req.subsonic_username = data.subsonic_username.trim()
      }
      if (data.subsonic_password) {
        req.subsonic_password = data.subsonic_password
      }
      await updateProfile(profile.id, req)
      await refreshProfiles()
      showToast('success', `Profile "${profile.display_name}" updated`)
      setMode('list')
    } finally {
      setSaving(false)
    }
  }, [updateProfile, refreshProfiles, showToast])

  const handleDeleteConfirm = useCallback(async () => {
    if (!confirmDelete) return
    setDeleting(true)
    try {
      await deleteProfile(confirmDelete.id)
      await refreshProfiles()
      showToast('success', `Profile "${confirmDelete.display_name}" deleted`)
      setConfirmDelete(null)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to delete profile')
    } finally {
      setDeleting(false)
    }
  }, [confirmDelete, deleteProfile, refreshProfiles, showToast])

  if (loading && profiles.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (mode === 'create') {
    return (
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-text">New Profile</h3>
        <ProfileForm
          saving={saving}
          onSave={handleCreate}
          onCancel={() => setMode('list')}
        />
      </div>
    )
  }

  if (typeof mode === 'object' && 'edit' in mode) {
    const profile = mode.edit
    const isShared = profile.display_name === SHARED_PROFILE_NAME
    const initial: ProfileFormData = {
      display_name: profile.display_name,
      subsonic_url: profile.subsonic_url ?? '',
      subsonic_username: profile.subsonic_username ?? '',
      subsonic_password: '',
    }
    return (
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-text">Edit Profile</h3>
        <ProfileForm
          initial={initial}
          isShared={isShared}
          saving={saving}
          hasServerPassword={profile.has_subsonic_password}
          onSave={(data) => handleUpdate(profile, data)}
          onCancel={() => setMode('list')}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-muted">
          {profiles.length} {profiles.length === 1 ? 'profile' : 'profiles'}
        </p>
        <motion.button
          onClick={() => setMode('create')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn-primary flex items-center gap-1.5 px-4 py-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Profile
        </motion.button>
      </div>

      {/* Profile list */}
      <AnimatePresence>
        <div className="space-y-2">
          {profiles.map((profile) => (
            <motion.div
              key={profile.id}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
            >
              <ProfileRow
                profile={profile}
                onEdit={(p) => setMode({ edit: p })}
                onDelete={(p) => setConfirmDelete(p)}
              />
            </motion.div>
          ))}
        </div>
      </AnimatePresence>

      {profiles.length === 0 && (
        <p className="text-sm text-text-muted text-center py-6">No profiles yet. Add one to get started.</p>
      )}

      {/* Delete confirmation */}
      <AnimatePresence>
        {confirmDelete && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
            onClick={(e) => { if (e.target === e.currentTarget) setConfirmDelete(null) }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="bg-surface border border-border rounded-xl p-6 w-full max-w-sm mx-4 shadow-xl"
            >
              <h2 className="text-lg font-semibold text-text mb-2">Delete Profile</h2>
              <p className="text-sm text-text-muted mb-6">
                Are you sure you want to delete <span className="text-text font-medium">"{confirmDelete.display_name}"</span>? This cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setConfirmDelete(null)}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-text-muted hover:text-text hover:bg-surface-hover rounded-lg transition-all duration-200"
                >
                  Cancel
                </button>
                <motion.button
                  onClick={handleDeleteConfirm}
                  disabled={deleting}
                  whileHover={!deleting ? { scale: 1.02 } : {}}
                  whileTap={!deleting ? { scale: 0.98 } : {}}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-red-600 hover:bg-red-500 text-white rounded-lg transition-all duration-200 disabled:opacity-50"
                >
                  {deleting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Saved indicator (hidden, kept for test accessibility) */}
      <div aria-live="polite" className="sr-only">
        {!saving && mode === 'list' && <CheckCircle className="hidden" />}
      </div>
    </div>
  )
}
