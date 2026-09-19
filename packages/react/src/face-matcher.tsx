'use client'

import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useDeepGuard } from './provider'
import type { FaceMatchResult } from './types'

export function FaceMatcher({
  onResult,
}: {
  onResult?: (result: FaceMatchResult) => void
}) {
  const { apiUrl } = useDeepGuard()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<FaceMatchResult | null>(null)
  const [selfie, setSelfie] = useState<File | null>(null)
  const [idPhoto, setIdPhoto] = useState<File | null>(null)

  const onDropSelfie = useCallback((files: File[]) => setSelfie(files[0] || null), [])
  const onDropId = useCallback((files: File[]) => setIdPhoto(files[0] || null), [])

  const dropSelfie = useDropzone({ onDrop: onDropSelfie, accept: { 'image/*': [] }, maxFiles: 1 })
  const dropId = useDropzone({ onDrop: onDropId, accept: { 'image/*': [] }, maxFiles: 1 })

  const handleMatch = async () => {
    if (!selfie || !idPhoto) return
    setLoading(true)
    try {
      const form = new FormData()
      form.append('selfie', selfie)
      form.append('id_photo', idPhoto)
      const res = await fetch(`${apiUrl}/match-faces`, { method: 'POST', body: form })
      const data: FaceMatchResult = await res.json()
      setResult(data)
      onResult?.(data)
    } catch (err) {
      console.error('Face match failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div {...dropSelfie.getRootProps()} className="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer">
          <input {...dropSelfie.getInputProps()} />
          <p className="text-sm">{selfie ? selfie.name : 'Drop selfie'}</p>
        </div>
        <div {...dropId.getRootProps()} className="border-2 border-dashed rounded-lg p-4 text-center cursor-pointer">
          <input {...dropId.getInputProps()} />
          <p className="text-sm">{idPhoto ? idPhoto.name : 'Drop ID photo'}</p>
        </div>
      </div>

      <button
        onClick={handleMatch}
        disabled={!selfie || !idPhoto || loading}
        className="w-full py-2 rounded-lg bg-primary text-primary-foreground disabled:opacity-50"
      >
        {loading ? 'Matching...' : 'Compare Faces'}
      </button>

      {result && (
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium">{result.match ? 'MATCH' : 'NO MATCH'}</span>
            <span className="text-sm text-muted-foreground">
              distance: {result.distance.toFixed(3)} | model: {result.model}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
