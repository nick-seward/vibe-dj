import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from 'react'
import { MusicTab } from '@/components/MusicTab'
import { ToastProvider } from '@/context/ToastContext'
import type { JobStatusResponse } from '@/types'

interface MotionDivProps extends HTMLAttributes<HTMLDivElement> { children?: ReactNode }
interface MotionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { children?: ReactNode }
interface MotionPProps extends HTMLAttributes<HTMLParagraphElement> { children?: ReactNode }

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: MotionDivProps) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: MotionButtonProps) => <button {...props}>{children}</button>,
    p: ({ children, ...props }: MotionPProps) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
}))

// Default mocks
const mockStartIndexing = vi.fn()
const mockCancelIndexing = vi.fn()
const mockValidatePath = vi.fn()
const mockClearValidation = vi.fn()
const mockSaveConfig = vi.fn().mockResolvedValue({ success: true, message: 'Saved' })

let mockIndexingState = {
  jobId: null as string | null,
  status: null as JobStatusResponse | null,
  isIndexing: false,
  error: null as string | null,
  startIndexing: mockStartIndexing,
  cancelIndexing: mockCancelIndexing,
}

vi.mock('@/hooks/useIndexing', () => ({
  useIndexing: () => mockIndexingState,
}))

vi.mock('@/hooks/useConfig', () => ({
  useValidatePath: () => ({
    validating: false,
    validation: { valid: true, exists: true, is_directory: true, message: 'Path is valid' },
    validatePath: mockValidatePath,
    clearValidation: mockClearValidation,
  }),
  useSaveConfig: () => ({
    saving: false,
    result: null,
    saveConfig: mockSaveConfig,
    clearResult: vi.fn(),
  }),
}))

const renderMusicTab = () => {
  return render(
    <ToastProvider>
      <MusicTab
        musicLibrary="/test/music"
        originalMusicLibrary="/test/music"
        onMusicLibraryChange={vi.fn()}
        onSaveSuccess={vi.fn()}
      />
    </ToastProvider>
  )
}

describe('MusicTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIndexingState = {
      jobId: null,
      status: null,
      isIndexing: false,
      error: null,
      startIndexing: mockStartIndexing,
      cancelIndexing: mockCancelIndexing,
    }
  })

  describe('progress display', () => {
    it('shows progress bar with processed/total when available', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: {
            phase: 'metadata',
            message: 'Extracting metadata (5/10)',
            processed: 5,
            total: 10,
          },
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Extracting metadata (5/10)')).toBeInTheDocument()
      expect(screen.getByText('5 / 10')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('shows progress bar at correct percentage for features phase', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: {
            phase: 'features',
            message: 'Analyzing audio (75/100)',
            processed: 75,
            total: 100,
          },
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Analyzing audio (75/100)')).toBeInTheDocument()
      expect(screen.getByText('75 / 100')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('does not show progress bar when no processed/total data', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: {
            phase: 'scanning',
            message: 'Scanning music library...',
          },
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Scanning music library...')).toBeInTheDocument()
      expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    })

    it('shows queued message before indexing starts', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'queued',
          progress: null,
          error: null,
          started_at: null,
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Waiting to start...')).toBeInTheDocument()
    })

    it('shows fallback message when running with no progress details', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: null,
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Indexing in progress...')).toBeInTheDocument()
    })
  })

  describe('error display', () => {
    it('shows error message when indexing fails', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: false,
        error: 'Library path does not exist',
      }

      renderMusicTab()

      expect(screen.getByText('Library path does not exist')).toBeInTheDocument()
    })

    it('does not show error while indexing is in progress', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        error: 'Some transient error',
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: null,
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      // Error should not be visible while indexing
      expect(screen.queryByText('Some transient error')).not.toBeInTheDocument()
    })
  })

  describe('index button', () => {
    it('shows spinner when indexing', () => {
      mockIndexingState = {
        ...mockIndexingState,
        isIndexing: true,
        jobId: 'test-job',
        status: {
          job_id: 'test-job',
          status: 'running',
          progress: null,
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        },
      }

      renderMusicTab()

      expect(screen.getByText('Indexing...')).toBeInTheDocument()
    })

    it('shows normal label when not indexing', () => {
      renderMusicTab()

      expect(screen.getByText('Index Music Library')).toBeInTheDocument()
    })
  })
})
