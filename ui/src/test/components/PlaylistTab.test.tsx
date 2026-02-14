import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react'
import { PlaylistTab } from '@/components/PlaylistTab'
import { ToastProvider } from '@/context/ToastContext'

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

const mockSaveConfig = vi.fn().mockResolvedValue({ success: true, message: 'Configuration saved successfully' })

vi.mock('@/hooks/useConfig', () => ({
  useSaveConfig: () => ({
    saving: false,
    result: null,
    saveConfig: mockSaveConfig,
    clearResult: vi.fn(),
  }),
}))

const defaultProps = {
  defaultPlaylistSize: 20,
  defaultBpmJitter: 5.0,
  originalPlaylistSize: 20,
  originalBpmJitter: 5.0,
  onPlaylistSizeChange: vi.fn(),
  onBpmJitterChange: vi.fn(),
  onSaveSuccess: vi.fn(),
}

const renderPlaylistTab = (overrides: Partial<typeof defaultProps> = {}) => {
  return render(
    <ToastProvider>
      <PlaylistTab {...defaultProps} {...overrides} />
    </ToastProvider>
  )
}

describe('PlaylistTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSaveConfig.mockResolvedValue({ success: true, message: 'Configuration saved successfully' })
  })

  describe('rendering', () => {
    it('renders playlist size dropdown with label', () => {
      renderPlaylistTab()

      expect(screen.getByLabelText(/default playlist size/i)).toBeInTheDocument()
    })

    it('renders BPM jitter slider with label', () => {
      renderPlaylistTab()

      expect(screen.getByLabelText(/bpm jitter/i)).toBeInTheDocument()
    })

    it('renders Save button', () => {
      renderPlaylistTab()

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
    })

    it('renders BPM variation preview section', () => {
      renderPlaylistTab()

      expect(screen.getByText('BPM Variation Preview')).toBeInTheDocument()
    })

    it('renders all playlist size options', () => {
      renderPlaylistTab()

      const dropdown = screen.getByLabelText(/default playlist size/i)
      const options = dropdown.querySelectorAll('option')
      const values = Array.from(options).map((o) => Number(o.value))

      expect(values).toEqual([15, 20, 25, 30, 35, 40])
    })

    it('displays current playlist size value', () => {
      renderPlaylistTab({ defaultPlaylistSize: 30, originalPlaylistSize: 30 })

      const dropdown = screen.getByLabelText(/default playlist size/i) as HTMLSelectElement
      expect(dropdown.value).toBe('30')
    })

    it('displays current BPM jitter value', () => {
      renderPlaylistTab({ defaultBpmJitter: 12.5, originalBpmJitter: 12.5 })

      expect(screen.getByText('12.5')).toBeInTheDocument()
    })

    it('shows tight/loose labels on slider', () => {
      renderPlaylistTab()

      expect(screen.getByText(/tight/i)).toBeInTheDocument()
      expect(screen.getByText(/loose/i)).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onPlaylistSizeChange when dropdown changes', () => {
      const onPlaylistSizeChange = vi.fn()
      renderPlaylistTab({ onPlaylistSizeChange })

      const dropdown = screen.getByLabelText(/default playlist size/i)
      fireEvent.change(dropdown, { target: { value: '35' } })

      expect(onPlaylistSizeChange).toHaveBeenCalledWith(35)
    })

    it('calls onBpmJitterChange when slider changes', () => {
      const onBpmJitterChange = vi.fn()
      renderPlaylistTab({ onBpmJitterChange })

      const slider = screen.getByLabelText(/bpm jitter/i)
      fireEvent.change(slider, { target: { value: '10' } })

      expect(onBpmJitterChange).toHaveBeenCalledWith(10)
    })
  })

  describe('save behavior', () => {
    it('disables Save button when no changes made', () => {
      renderPlaylistTab()

      const saveButton = screen.getByRole('button', { name: /save/i })
      expect(saveButton).toBeDisabled()
    })

    it('enables Save button when playlist size changes', () => {
      renderPlaylistTab({ defaultPlaylistSize: 30, originalPlaylistSize: 20 })

      const saveButton = screen.getByRole('button', { name: /save/i })
      expect(saveButton).not.toBeDisabled()
    })

    it('enables Save button when BPM jitter changes', () => {
      renderPlaylistTab({ defaultBpmJitter: 10.0, originalBpmJitter: 5.0 })

      const saveButton = screen.getByRole('button', { name: /save/i })
      expect(saveButton).not.toBeDisabled()
    })

    it('calls saveConfig with only changed playlist size', async () => {
      renderPlaylistTab({ defaultPlaylistSize: 30, originalPlaylistSize: 20 })

      const saveButton = screen.getByRole('button', { name: /save/i })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSaveConfig).toHaveBeenCalledWith({ default_playlist_size: 30 })
      })
    })

    it('calls saveConfig with only changed BPM jitter', async () => {
      renderPlaylistTab({ defaultBpmJitter: 12.0, originalBpmJitter: 5.0 })

      const saveButton = screen.getByRole('button', { name: /save/i })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSaveConfig).toHaveBeenCalledWith({ default_bpm_jitter: 12.0 })
      })
    })

    it('calls saveConfig with both fields when both changed', async () => {
      renderPlaylistTab({
        defaultPlaylistSize: 35,
        originalPlaylistSize: 20,
        defaultBpmJitter: 15.0,
        originalBpmJitter: 5.0,
      })

      const saveButton = screen.getByRole('button', { name: /save/i })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSaveConfig).toHaveBeenCalledWith({
          default_playlist_size: 35,
          default_bpm_jitter: 15.0,
        })
      })
    })

    it('calls onSaveSuccess after successful save', async () => {
      const onSaveSuccess = vi.fn()
      renderPlaylistTab({
        defaultPlaylistSize: 30,
        originalPlaylistSize: 20,
        onSaveSuccess,
      })

      const saveButton = screen.getByRole('button', { name: /save/i })
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSaveConfig).toHaveBeenCalled()
      })

      // onSaveSuccess is called after a 2s setTimeout
      await waitFor(() => {
        expect(onSaveSuccess).toHaveBeenCalled()
      }, { timeout: 3000 })
    })
  })

  describe('BPM variation preview text', () => {
    it('shows tight message for low jitter', () => {
      renderPlaylistTab({ defaultBpmJitter: 1.0, originalBpmJitter: 1.0 })

      expect(screen.getByText(/stay close to the target bpm/i)).toBeInTheDocument()
    })

    it('shows moderate message for mid jitter', () => {
      renderPlaylistTab({ defaultBpmJitter: 10.0, originalBpmJitter: 10.0 })

      expect(screen.getByText(/moderate bpm variation/i)).toBeInTheDocument()
    })

    it('shows wide message for high jitter', () => {
      renderPlaylistTab({ defaultBpmJitter: 18.0, originalBpmJitter: 18.0 })

      expect(screen.getByText(/wide bpm swings/i)).toBeInTheDocument()
    })
  })
})
