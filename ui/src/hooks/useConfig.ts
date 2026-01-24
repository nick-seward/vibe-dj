import { useState, useCallback, useEffect } from 'react'
import type { ConfigResponse, ValidatePathResponse, TestNavidromeResponse, UpdateConfigRequest, UpdateConfigResponse } from '@/types'

const API_BASE = '/api'

interface UseConfigState {
  config: ConfigResponse | null
  loading: boolean
  error: string | null
}

export function useConfig() {
  const [state, setState] = useState<UseConfigState>({
    config: null,
    loading: false,
    error: null,
  })

  const fetchConfig = useCallback(async (): Promise<ConfigResponse> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/config`)

      if (!response.ok) {
        throw new Error(`Failed to fetch config: ${response.statusText}`)
      }

      const data: ConfigResponse = await response.json()
      setState({ config: data, loading: false, error: null })
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch config'
      setState({ config: null, loading: false, error: errorMessage })
      throw err
    }
  }, [])

  useEffect(() => {
    fetchConfig().catch(() => {
      // Error is handled in state
    })
  }, [fetchConfig])

  return { ...state, fetchConfig }
}

export function useValidatePath() {
  const [validating, setValidating] = useState(false)
  const [validation, setValidation] = useState<ValidatePathResponse | null>(null)

  const validatePath = useCallback(async (path: string): Promise<ValidatePathResponse> => {
    setValidating(true)

    try {
      const response = await fetch(`${API_BASE}/config/validate-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })

      if (!response.ok) {
        throw new Error(`Validation failed: ${response.statusText}`)
      }

      const data: ValidatePathResponse = await response.json()
      setValidation(data)
      setValidating(false)
      return data
    } catch (err) {
      const errorResult: ValidatePathResponse = {
        valid: false,
        exists: false,
        is_directory: false,
        message: err instanceof Error ? err.message : 'Validation failed',
      }
      setValidation(errorResult)
      setValidating(false)
      return errorResult
    }
  }, [])

  const clearValidation = useCallback(() => {
    setValidation(null)
  }, [])

  return { validating, validation, validatePath, clearValidation }
}

export function useTestNavidrome() {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<TestNavidromeResponse | null>(null)

  const testConnection = useCallback(async (
    url: string,
    username: string,
    password: string
  ): Promise<TestNavidromeResponse> => {
    setTesting(true)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE}/navidrome/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, username, password }),
      })

      if (!response.ok) {
        throw new Error(`Test failed: ${response.statusText}`)
      }

      const data: TestNavidromeResponse = await response.json()
      setResult(data)
      setTesting(false)
      return data
    } catch (err) {
      const errorResult: TestNavidromeResponse = {
        success: false,
        message: err instanceof Error ? err.message : 'Connection test failed',
      }
      setResult(errorResult)
      setTesting(false)
      return errorResult
    }
  }, [])

  const clearResult = useCallback(() => {
    setResult(null)
  }, [])

  return { testing, result, testConnection, clearResult }
}

export function useSaveConfig() {
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState<UpdateConfigResponse | null>(null)

  const saveConfig = useCallback(async (
    updates: UpdateConfigRequest
  ): Promise<UpdateConfigResponse> => {
    setSaving(true)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })

      if (!response.ok) {
        throw new Error(`Save failed: ${response.statusText}`)
      }

      const data: UpdateConfigResponse = await response.json()
      setResult(data)
      setSaving(false)
      return data
    } catch (err) {
      const errorResult: UpdateConfigResponse = {
        success: false,
        message: err instanceof Error ? err.message : 'Failed to save configuration',
      }
      setResult(errorResult)
      setSaving(false)
      return errorResult
    }
  }, [])

  const clearResult = useCallback(() => {
    setResult(null)
  }, [])

  return { saving, result, saveConfig, clearResult }
}
