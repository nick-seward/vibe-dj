import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react'
import { ProfilesTab } from '@/components/ProfilesTab'
import { ToastProvider } from '@/context/ToastContext'
import type { Profile } from '@/types'

interface MotionDivProps extends HTMLAttributes<HTMLDivElement> { children?: ReactNode }
interface MotionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { children?: ReactNode }

vi.mock('@/hooks/useConfig', () => ({
  useTestNavidrome: () => ({
    testing: false,
    result: null,
    testConnection: vi.fn().mockResolvedValue({ success: true, message: 'Connected' }),
    clearResult: vi.fn(),
  }),
}))

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: MotionDivProps) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: MotionButtonProps) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
}))

const makeProfile = (id: number, display_name: string, extra: Partial<Profile> = {}): Profile => ({
  id,
  display_name,
  subsonic_url: null,
  subsonic_username: null,
  has_subsonic_password: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  ...extra,
})

const mockCreateProfile = vi.fn()
const mockUpdateProfile = vi.fn()
const mockDeleteProfile = vi.fn()
const mockRefreshProfiles = vi.fn()
const mockSetActiveProfileId = vi.fn()

let mockProfiles: Profile[] = []

vi.mock('@/context/ProfileContext', () => ({
  useProfileContext: () => ({
    profiles: mockProfiles,
    activeProfileId: 1,
    activeProfile: mockProfiles[0] ?? null,
    loading: false,
    error: null,
    setActiveProfileId: mockSetActiveProfileId,
    refreshProfiles: mockRefreshProfiles,
    createProfile: mockCreateProfile,
    updateProfile: mockUpdateProfile,
    deleteProfile: mockDeleteProfile,
  }),
}))

const renderWithProviders = (ui: React.ReactElement) =>
  render(<ToastProvider>{ui}</ToastProvider>)

describe('ProfilesTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockProfiles = [
      makeProfile(1, 'Shared'),
      makeProfile(2, 'Nick', { subsonic_url: 'http://localhost:4533', subsonic_username: 'nick' }),
    ]
    mockCreateProfile.mockResolvedValue(makeProfile(3, 'Family'))
    mockUpdateProfile.mockResolvedValue(makeProfile(2, 'Nick'))
    mockDeleteProfile.mockResolvedValue(undefined)
    mockRefreshProfiles.mockResolvedValue(undefined)
  })

  it('renders the list of profiles', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByText('Shared')).toBeInTheDocument()
    expect(screen.getByText('Nick')).toBeInTheDocument()
  })

  it('shows profile count', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByText('2 profiles')).toBeInTheDocument()
  })

  it('shows Add Profile button', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByRole('button', { name: /add profile/i })).toBeInTheDocument()
  })

  it('shows Edit button for each profile', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByRole('button', { name: /edit shared/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /edit nick/i })).toBeInTheDocument()
  })

  it('shows Delete button for each profile', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByRole('button', { name: /delete shared/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /delete nick/i })).toBeInTheDocument()
  })

  it('disables Delete button for Shared profile', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByRole('button', { name: /delete shared/i })).toBeDisabled()
  })

  it('enables Delete button for non-Shared profiles', () => {
    renderWithProviders(<ProfilesTab />)
    expect(screen.getByRole('button', { name: /delete nick/i })).not.toBeDisabled()
  })

  it('shows create form when Add Profile is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /add profile/i }))

    expect(screen.getByText('New Profile')).toBeInTheDocument()
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
  })

  it('creates a profile with display name', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /add profile/i }))
    await user.type(screen.getByLabelText(/display name/i), 'Family')
    await user.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() => {
      expect(mockCreateProfile).toHaveBeenCalledWith(
        expect.objectContaining({ display_name: 'Family' })
      )
      expect(mockRefreshProfiles).toHaveBeenCalled()
    })
  })

  it('returns to list after successful create', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /add profile/i }))
    await user.type(screen.getByLabelText(/display name/i), 'Family')
    await user.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() => {
      expect(screen.queryByText('New Profile')).not.toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add profile/i })).toBeInTheDocument()
    })
  })

  it('shows validation error when display name is empty on create', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /add profile/i }))
    await user.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() => {
      expect(screen.getByText('Display name is required')).toBeInTheDocument()
    })
    expect(mockCreateProfile).not.toHaveBeenCalled()
  })

  it('cancels create form and returns to list', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /add profile/i }))
    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(screen.queryByText('New Profile')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /add profile/i })).toBeInTheDocument()
  })

  it('shows edit form with pre-filled values when Edit is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /edit nick/i }))

    expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    const nameInput = screen.getByLabelText(/display name/i) as HTMLInputElement
    expect(nameInput.value).toBe('Nick')
  })

  it('disables display name field when editing Shared profile', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /edit shared/i }))

    const nameInput = screen.getByLabelText(/display name/i)
    expect(nameInput).toBeDisabled()
  })

  it('saves updated profile', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /edit nick/i }))

    const nameInput = screen.getByLabelText(/display name/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Nicholas')
    await user.click(screen.getByRole('button', { name: /^save$/i }))

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith(2, expect.objectContaining({ display_name: 'Nicholas' }))
      expect(mockRefreshProfiles).toHaveBeenCalled()
    })
  })

  it('shows delete confirmation dialog when Delete is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /delete nick/i }))

    expect(screen.getByText('Delete Profile')).toBeInTheDocument()
    expect(screen.getByText(/"Nick"/)).toBeInTheDocument()
  })

  it('deletes profile after confirmation', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /delete nick/i }))
    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => {
      expect(mockDeleteProfile).toHaveBeenCalledWith(2)
      expect(mockRefreshProfiles).toHaveBeenCalled()
    })
  })

  it('cancels delete and closes dialog', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProfilesTab />)

    await user.click(screen.getByRole('button', { name: /delete nick/i }))
    await user.click(screen.getByRole('button', { name: /cancel/i }))

    await waitFor(() => {
      expect(screen.queryByText('Delete Profile')).not.toBeInTheDocument()
    })
    expect(mockDeleteProfile).not.toHaveBeenCalled()
  })

  describe('SubSonic connection in profile form', () => {
    it('shows Test SubSonic Connection button in edit form', async () => {
      const user = userEvent.setup()
      renderWithProviders(<ProfilesTab />)

      await user.click(screen.getByRole('button', { name: /edit nick/i }))

      expect(screen.getByRole('button', { name: /test subsonic connection/i })).toBeInTheDocument()
    })

    it('Test Connection button is disabled when URL is missing', async () => {
      const user = userEvent.setup()
      renderWithProviders(<ProfilesTab />)

      await user.click(screen.getByRole('button', { name: /add profile/i }))

      // Fill in username and password but not URL
      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/^password$/i), 'testpass')

      expect(screen.getByRole('button', { name: /test subsonic connection/i })).toBeDisabled()
    })

    it('Test Connection button is disabled when username is missing', async () => {
      const user = userEvent.setup()
      renderWithProviders(<ProfilesTab />)

      await user.click(screen.getByRole('button', { name: /add profile/i }))

      // Fill in URL and password but not username
      await user.type(screen.getByLabelText(/subsonic url/i), 'http://localhost:4533')
      await user.type(screen.getByLabelText(/^password$/i), 'testpass')

      expect(screen.getByRole('button', { name: /test subsonic connection/i })).toBeDisabled()
    })

    it('Test Connection button is enabled when password is stored on server', async () => {
      const user = userEvent.setup()
      mockProfiles = [
        makeProfile(1, 'Shared'),
        makeProfile(2, 'Nick', {
          subsonic_url: 'http://localhost:4533',
          subsonic_username: 'nick',
          has_subsonic_password: true,
        }),
      ]
      renderWithProviders(<ProfilesTab />)

      await user.click(screen.getByRole('button', { name: /edit nick/i }))

      // URL and username are pre-filled; password is stored on server — button should be enabled
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /test subsonic connection/i })).not.toBeDisabled()
      })
    })

    it('Test Connection button is enabled when URL, username, and password are all filled', async () => {
      const user = userEvent.setup()
      renderWithProviders(<ProfilesTab />)

      await user.click(screen.getByRole('button', { name: /add profile/i }))

      await user.type(screen.getByLabelText(/subsonic url/i), 'http://localhost:4533')
      await user.type(screen.getByLabelText(/username/i), 'testuser')
      await user.type(screen.getByLabelText(/^password$/i), 'testpass')

      expect(screen.getByRole('button', { name: /test subsonic connection/i })).not.toBeDisabled()
    })
  })
})
