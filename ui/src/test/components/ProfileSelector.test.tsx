import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react'
import { ProfileSelector } from '@/components/ProfileSelector'
import type { Profile } from '@/types'

interface MotionDivProps extends HTMLAttributes<HTMLDivElement> { children?: ReactNode }
interface MotionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { children?: ReactNode }

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: MotionDivProps) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: MotionButtonProps) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
}))

const makeProfile = (id: number, display_name: string): Profile => ({
  id,
  display_name,
  subsonic_url: null,
  subsonic_username: null,
  has_subsonic_password: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
})

const mockSetActiveProfileId = vi.fn()
const mockCreateProfile = vi.fn()
const mockRefreshProfiles = vi.fn()

let mockProfiles: Profile[] = []
let mockActiveProfileId: number | null = null

vi.mock('@/context/ProfileContext', () => ({
  useProfileContext: () => ({
    profiles: mockProfiles,
    activeProfileId: mockActiveProfileId,
    activeProfile: mockProfiles.find((p) => p.id === mockActiveProfileId) ?? null,
    loading: false,
    error: null,
    setActiveProfileId: mockSetActiveProfileId,
    refreshProfiles: mockRefreshProfiles,
    createProfile: mockCreateProfile,
    updateProfile: vi.fn(),
    deleteProfile: vi.fn(),
  }),
}))

describe('ProfileSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockProfiles = [makeProfile(1, 'Shared'), makeProfile(2, 'Nick')]
    mockActiveProfileId = 1
    mockCreateProfile.mockResolvedValue(makeProfile(3, 'Family'))
    mockRefreshProfiles.mockResolvedValue(undefined)
  })

  it('renders the active profile display name', () => {
    render(<ProfileSelector />)
    expect(screen.getByText('Shared')).toBeInTheDocument()
  })

  it('shows "Select Profile" when no active profile is set', () => {
    mockActiveProfileId = null
    render(<ProfileSelector />)
    expect(screen.getByText('Select Profile')).toBeInTheDocument()
  })

  it('opens dropdown when button is clicked', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))

    expect(screen.getByRole('listbox', { name: /profile list/i })).toBeInTheDocument()
    expect(screen.getAllByText('Shared').length).toBeGreaterThan(0)
    expect(screen.getByText('Nick')).toBeInTheDocument()
  })

  it('shows all profiles in the dropdown', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))

    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(2)
  })

  it('marks the active profile with aria-selected', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))

    const options = screen.getAllByRole('option')
    const sharedOption = options.find((o) => o.textContent?.includes('Shared'))
    expect(sharedOption).toHaveAttribute('aria-selected', 'true')
  })

  it('calls setActiveProfileId when a profile is selected', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByRole('option', { name: /nick/i }))

    expect(mockSetActiveProfileId).toHaveBeenCalledWith(2)
  })

  it('closes dropdown after selecting a profile', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByRole('option', { name: /nick/i }))

    await waitFor(() => {
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })
  })

  it('shows "Add New Profile" option in dropdown', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))

    expect(screen.getByText('Add New Profile')).toBeInTheDocument()
  })

  it('opens add profile modal when "Add New Profile" is clicked', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByText('Add New Profile'))

    await waitFor(() => {
      expect(screen.getByText('Add New Profile', { selector: 'h2' })).toBeInTheDocument()
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
    })
  })

  it('creates a new profile and sets it active', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByText('Add New Profile'))

    await waitFor(() => {
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/display name/i), 'Family')
    await user.click(screen.getByRole('button', { name: /add profile/i }))

    await waitFor(() => {
      expect(mockCreateProfile).toHaveBeenCalledWith({ display_name: 'Family' })
      expect(mockRefreshProfiles).toHaveBeenCalled()
      expect(mockSetActiveProfileId).toHaveBeenCalledWith(3)
    })
  })

  it('shows error in modal when display name is empty', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByText('Add New Profile'))

    await waitFor(() => {
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /add profile/i }))

    await waitFor(() => {
      expect(screen.getByText('Display name is required')).toBeInTheDocument()
    })
    expect(mockCreateProfile).not.toHaveBeenCalled()
  })

  it('closes modal when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(<ProfileSelector />)

    await user.click(screen.getByRole('button', { name: /select active profile/i }))
    await user.click(screen.getByText('Add New Profile'))

    await waitFor(() => {
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    await waitFor(() => {
      expect(screen.queryByLabelText(/display name/i)).not.toBeInTheDocument()
    })
  })
})
