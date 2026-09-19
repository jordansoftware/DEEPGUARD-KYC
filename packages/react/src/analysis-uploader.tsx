'use client'

import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useDeepGuard } from './provider'
import type { AnalysisResult } from './types'

export function AnalysisUploader({
  onResult,
}: {
  onResult?: (result: AnalysisResult) => void
}) {
  const { apiUrl } = useDeepGuard()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0]
      if (!file) return

      setLoading(true)
      try {
        const form = new FormData()
        form.append('file', file)
        const res = await fetch(`${apiUrl}/analyze`, { method: 'POST', body: form })
        const data: AnalysisResult = await res.json()
        setResult(data)
        onResult?.(data)
      } catch (err) {
        console.error('DeepGuard analysis failed:', err)
      } finally {
        setLoading(false)
      }
    },
    [apiUrl, onResult]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'] },
    maxFiles: 1,
    maxSize: 30 * 1024 * 1024,
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-primary/50"
      >
        <input {...getInputProps()} />
        {loading ? (
          <p>Analyzing...</p>
        ) : isDragActive ? (
          <p>Drop the document here...</p>
        ) : (
          <p>Drag & drop a document, or click to select</p>
        )}
      </div>

      {result && (
        <div className="rounded-lg border p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">Score: {result.score}/100</span>
            <span
              className={`px-2 py-1 rounded text-sm ${
                result.verdict === 'authentique'
                  ? 'bg-green-100 text-green-800'
                  : result.verdict === 'suspect'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
              }`}
            >
              {result.verdict_label}
            </span>
          </div>
          {result.reasons.length > 0 && (
            <ul className="text-sm text-muted-foreground space-y-1">
              {result.reasons.map((r, i) => (
                <li key={i}>- {r}</li>
              ))}
            </ul>
          )}
          {result.heatmap && (
            <img src={result.heatmap} alt="Forensic heatmap" className="rounded mt-2" />
          )}
        </div>
      )}
    </div>
  )
}
