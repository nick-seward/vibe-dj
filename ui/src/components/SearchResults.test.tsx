import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchResults } from './SearchResults'
import { ChoiceListProvider } from '@/context/ChoiceListContext'
import type { PaginatedSearchResult, PageSize } from '@/types'

const mockResults: PaginatedSearchResult = {
  songs: [
    {
      id: 1,
      file_path: '/test/song1.mp3',
      title: 'Test Song 1',
      artist: 'Test Artist 1',
      album: 'Test Album 1',
      genre: 'Rock',
      duration: 180,
      last_modified: 1234567890,
    },
    {
      id: 2,
      file_path: '/test/song2.mp3',
      title: 'Test Song 2',
      artist: 'Test Artist 2',
      album: 'Test Album 2',
      genre: 'Pop',
      duration: 200,
      last_modified: 1234567891,
    },
  ],
  total: 100,
  limit: 50,
  offset: 0,
}

const renderWithProvider = (ui: React.ReactElement) => {
  return render(<ChoiceListProvider>{ui}</ChoiceListProvider>)
}

describe('SearchResults', () => {
  const defaultProps = {
    results: mockResults,
    pageSize: 50 as PageSize,
    onPageSizeChange: vi.fn(),
    onPageChange: vi.fn(),
    onBack: vi.fn(),
    onGeneratePlaylist: vi.fn(),
    loading: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search results with pagination info', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    expect(screen.getByText(/showing 1-2 of 100/i)).toBeInTheDocument()
  })

  it('renders page size dropdown with correct options', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    expect(dropdown).toBeInTheDocument()
    expect(dropdown).toHaveValue('50')

    expect(screen.getByRole('option', { name: '50' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '100' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '150' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '200' })).toBeInTheDocument()
  })

  it('calls onPageSizeChange when dropdown value changes', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    fireEvent.change(dropdown, { target: { value: '100' } })

    expect(defaultProps.onPageSizeChange).toHaveBeenCalledWith(100)
  })

  it('renders pagination controls when there are multiple pages', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
  })

  it('disables previous button on first page', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const prevButton = screen.getByRole('button', { name: /previous/i })
    expect(prevButton).toBeDisabled()
  })

  it('enables next button when there are more pages', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    expect(nextButton).not.toBeDisabled()
  })

  it('calls onPageChange when next button is clicked', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    fireEvent.click(nextButton)

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(50)
  })

  it('calls onPageChange when previous button is clicked on page 2', () => {
    const propsOnPage2 = {
      ...defaultProps,
      results: { ...mockResults, offset: 50 },
    }
    renderWithProvider(<SearchResults {...propsOnPage2} />)

    const prevButton = screen.getByRole('button', { name: /previous/i })
    fireEvent.click(prevButton)

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(0)
  })

  it('shows limited message when total exceeds 1000', () => {
    const propsWithLargeTotal = {
      ...defaultProps,
      results: { ...mockResults, total: 2000 },
    }
    renderWithProvider(<SearchResults {...propsWithLargeTotal} />)

    expect(screen.getByText(/limited to 1000/i)).toBeInTheDocument()
  })

  it('does not show pagination controls when only one page', () => {
    const propsWithOnePage = {
      ...defaultProps,
      results: { ...mockResults, total: 30 },
    }
    renderWithProvider(<SearchResults {...propsWithOnePage} />)

    expect(screen.queryByText(/page \d+ of \d+/i)).not.toBeInTheDocument()
  })

  it('disables next button when at max search depth', () => {
    const propsAtMaxDepth = {
      ...defaultProps,
      results: { ...mockResults, offset: 950, total: 2000 },
    }
    renderWithProvider(<SearchResults {...propsAtMaxDepth} />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    expect(nextButton).toBeDisabled()
  })

  it('disables dropdown when loading', () => {
    const propsLoading = {
      ...defaultProps,
      loading: true,
    }
    renderWithProvider(<SearchResults {...propsLoading} />)

    const dropdown = screen.getByLabelText(/results per page/i)
    expect(dropdown).toBeDisabled()
  })

  it('disables pagination buttons when loading', () => {
    const propsLoading = {
      ...defaultProps,
      loading: true,
    }
    renderWithProvider(<SearchResults {...propsLoading} />)

    const nextButton = screen.getByRole('button', { name: /next/i })
    expect(nextButton).toBeDisabled()
  })

  it('shows no results message when songs array is empty', () => {
    const propsNoResults = {
      ...defaultProps,
      results: { ...mockResults, songs: [], total: 0 },
    }
    renderWithProvider(<SearchResults {...propsNoResults} />)

    expect(screen.getByText(/no songs found/i)).toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', () => {
    renderWithProvider(<SearchResults {...defaultProps} />)

    const backButton = screen.getByRole('button', { name: /back to search/i })
    fireEvent.click(backButton)

    expect(defaultProps.onBack).toHaveBeenCalled()
  })
})
