'use client'

import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useDeepGuard } from './provider'
import type { LivenessResult } from './types'

export function LivenessCheck({
  onResult,
}: {
  onResult?: (result: LivenessResult) => void
}) {
  const { apiUrl } = useDeepGuard()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<LivenessResult | null>(null)

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0]
      if (!file) return

      setLoading(true)
      try {
        const form = new FormData()
        form.append('file', file)
        const res = await fetch(`${apiUrl}/detect-liveness`, { method: 'POST', body: form })
        const data: LivenessResult = await res.json()
        setResult(data)
        onResult?.(data)
      } catch (err) {
        console.error('Liveness check failed:', err)
      } finally {
        setLoading(false)
      }
    },
    [apiUrl, onResult]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-primary/50"
      >
        <input {...getInputProps()} />
        {loading ? (
          <p>Checking liveness...</p>
        ) : isDragActive ? (
          <p>Drop face photo here...</p>
        ) : (
          <p>Drag & drop a face photo, or click to select</p>
        )}
      </div>

      {result && (
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">{result.is_live ? 'LIVE' : 'SPOOF'}</span>
            <span className="text-sm text-muted-foreground">score: {result.score.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
