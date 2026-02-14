import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react'
import { PlaylistView } from '@/components/PlaylistView'
import type { PlaylistResponse } from '@/types'

interface MotionDivProps extends HTMLAttributes<HTMLDivElement> { children?: ReactNode }
interface MotionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { children?: ReactNode }

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: MotionDivProps) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: MotionButtonProps) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
}))

const mockPlaylist: PlaylistResponse = {
  songs: [
    {
      id: 10,
      file_path: '/music/song1.mp3',
      title: 'Generated Song 1',
      artist: 'Artist A',
      album: 'Album X',
      genre: 'Rock',
      duration: 200,
      last_modified: 1234567890,
    },
    {
      id: 11,
      file_path: '/music/song2.mp3',
      title: 'Generated Song 2',
      artist: 'Artist B',
      album: 'Album Y',
      genre: 'Pop',
      duration: 180,
      last_modified: 1234567891,
    },
    {
      id: 12,
      file_path: '/music/song3.mp3',
      title: 'Generated Song 3',
      artist: 'Artist C',
      album: 'Album Z',
      genre: 'Jazz',
      duration: 240,
      last_modified: 1234567892,
    },
  ],
  seed_songs: [
    {
      id: 1,
      file_path: '/music/seed1.mp3',
      title: 'Seed Song 1',
      artist: 'Seed Artist',
      album: 'Seed Album',
      genre: 'Rock',
      duration: 210,
      last_modified: 1234567880,
    },
  ],
  created_at: '2026-02-13T20:00:00Z',
  length: 3,
}

const defaultProps = {
  playlist: mockPlaylist,
  onRegenerate: vi.fn().mockResolvedValue(undefined),
  onSyncToNavidrome: vi.fn().mockResolvedValue(true),
  onStartOver: vi.fn(),
  regenerating: false,
}

const renderPlaylistView = (overrides: Partial<typeof defaultProps> = {}) => {
  return render(<PlaylistView {...defaultProps} {...overrides} />)
}

describe('PlaylistView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders seed songs section', () => {
      renderPlaylistView()

      expect(screen.getByText(/based on your seeds/i)).toBeInTheDocument()
      expect(screen.getByText(/seed song 1/i)).toBeInTheDocument()
    })

    it('renders playlist songs with count', () => {
      renderPlaylistView()

      expect(screen.getByText('Your Playlist (3 songs)')).toBeInTheDocument()
      expect(screen.getByText('Generated Song 1')).toBeInTheDocument()
      expect(screen.getByText('Generated Song 2')).toBeInTheDocument()
      expect(screen.getByText('Generated Song 3')).toBeInTheDocument()
    })

    it('renders song artist and album info', () => {
      renderPlaylistView()

      expect(screen.getByText(/Artist A • Album X/)).toBeInTheDocument()
      expect(screen.getByText(/Artist B • Album Y/)).toBeInTheDocument()
    })

    it('renders numbered song list', () => {
      renderPlaylistView()

      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('renders Start Over button', () => {
      renderPlaylistView()

      expect(screen.getByText('Start Over')).toBeInTheDocument()
    })

    it('renders Regenerate button', () => {
      renderPlaylistView()

      expect(screen.getByText('Regenerate')).toBeInTheDocument()
    })

    it('renders Send to SubSonic button', () => {
      renderPlaylistView()

      expect(screen.getByText('Send to SubSonic')).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onStartOver when Start Over is clicked', () => {
      const onStartOver = vi.fn()
      renderPlaylistView({ onStartOver })

      fireEvent.click(screen.getByText('Start Over'))

      expect(onStartOver).toHaveBeenCalled()
    })

    it('calls onRegenerate when Regenerate is clicked', () => {
      const onRegenerate = vi.fn().mockResolvedValue(undefined)
      renderPlaylistView({ onRegenerate })

      fireEvent.click(screen.getByText('Regenerate'))

      expect(onRegenerate).toHaveBeenCalled()
    })

    it('disables Regenerate button while regenerating', () => {
      renderPlaylistView({ regenerating: true })

      const regenerateButton = screen.getByRole('button', { name: /regenerate/i })
      expect(regenerateButton).toBeDisabled()
    })
  })

  describe('sync modal', () => {
    it('opens modal when Send to SubSonic is clicked', async () => {
      const user = userEvent.setup()
      renderPlaylistView()

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })
    })

    it('shows Send and Cancel buttons in modal', async () => {
      const user = userEvent.setup()
      renderPlaylistView()

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /^send$/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      })
    })

    it('disables Send button when playlist name is empty', async () => {
      const user = userEvent.setup()
      renderPlaylistView()

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        const sendButton = screen.getByRole('button', { name: /^send$/i })
        expect(sendButton).toBeDisabled()
      })
    })

    it('enables Send button when playlist name is entered', async () => {
      const user = userEvent.setup()
      renderPlaylistView()

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByPlaceholderText(/enter playlist name/i), 'My Playlist')

      await waitFor(() => {
        const sendButton = screen.getByRole('button', { name: /^send$/i })
        expect(sendButton).not.toBeDisabled()
      })
    })

    it('calls onSyncToNavidrome with playlist name when Send is clicked', async () => {
      const onSyncToNavidrome = vi.fn().mockResolvedValue(true)
      const user = userEvent.setup()
      renderPlaylistView({ onSyncToNavidrome })

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByPlaceholderText(/enter playlist name/i), 'My Playlist')
      await user.click(screen.getByRole('button', { name: /^send$/i }))

      await waitFor(() => {
        expect(onSyncToNavidrome).toHaveBeenCalledWith('My Playlist')
      })
    })

    it('closes modal when Cancel is clicked', async () => {
      const user = userEvent.setup()
      renderPlaylistView()

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/enter playlist name/i)).not.toBeInTheDocument()
      })
    })

    it('shows success celebration after sync', async () => {
      const onSyncToNavidrome = vi.fn().mockResolvedValue(true)
      const user = userEvent.setup()
      renderPlaylistView({ onSyncToNavidrome })

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByPlaceholderText(/enter playlist name/i), 'Test Playlist')
      await user.click(screen.getByRole('button', { name: /^send$/i }))

      await waitFor(() => {
        expect(screen.getByText(/playlist sent to subsonic successfully/i)).toBeInTheDocument()
      })
    })

    it('disables Send to SubSonic button after successful sync', async () => {
      const onSyncToNavidrome = vi.fn().mockResolvedValue(true)
      const user = userEvent.setup()
      renderPlaylistView({ onSyncToNavidrome })

      await user.click(screen.getByText('Send to SubSonic'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/enter playlist name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByPlaceholderText(/enter playlist name/i), 'Test Playlist')
      await user.click(screen.getByRole('button', { name: /^send$/i }))

      await waitFor(() => {
        expect(screen.getByText('Sent!')).toBeInTheDocument()
        const sentButton = screen.getByRole('button', { name: /sent/i })
        expect(sentButton).toBeDisabled()
      })
    })
  })
})
