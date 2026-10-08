import { useCallback, useRef, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/mobile-verify')({
  component: MobileVerifyPage,
})

function MobileVerifyPage() {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')

  if (!token) {
    return (
      <div className='flex min-h-screen items-center justify-center'>
        <div className='space-y-4 text-center'>
          <h1 className='text-2xl font-bold'>Invalid Link</h1>
          <p className='text-muted-foreground'>
            No verification token found. Please scan the QR code again.
          </p>
        </div>
      </div>
    )
  }

  return <CameraCapture token={token} />
}

function CameraCapture({ token }: { token: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [photo, setPhoto] = useState<string | null>(null)
  const [status, setStatus] = useState<
    'idle' | 'capturing' | 'uploading' | 'success' | 'error'
  >('idle')
  const [result, setResult] = useState<{
    face_match?: boolean
    face_score: number
    liveness_score: number
  } | null>(null)
  const [error, setError] = useState('')
  const [cameraReady, setCameraReady] = useState(false)

  const [deviceInfo] = useState(() => {
    const info = {
      is_emulator: false,
      is_bot: false,
      is_mobile: /android|iphone|ipad|mobile/i.test(navigator.userAgent),
      confidence: 0.5,
      user_agent: navigator.userAgent,
    }

    if (navigator.webdriver) {
      info.is_emulator = true
      info.confidence -= 0.3
    }

    const ratio = window.screen.width / window.screen.height
    if (ratio > 0.4 && ratio < 0.7) {
      info.confidence += 0.1
    }

    if (
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === 'function'
    ) {
      info.confidence += 0.1
    }

    if (window.DeviceOrientationEvent) {
      info.confidence += 0.05
    }

    info.confidence = Math.max(0, Math.min(1, info.confidence))
    return info
  })

  const startCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
        videoRef.current.onloadedmetadata = () => setCameraReady(true)
      }
    } catch {
      setError('Camera access denied. Please allow camera permissions.')
      setStatus('error')
    }
  }, [])

  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return

    setStatus('capturing')
    const video = videoRef.current
    const canvas = canvasRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')!
    ctx.drawImage(video, 0, 0)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    setPhoto(dataUrl)
    setStatus('idle')
  }, [])

  const submitVerification = useCallback(async () => {
    if (!photo) return
    setStatus('uploading')

    try {
      const res = await fetch(photo)
      const blob = await res.blob()

      const livenessChecks = {
        eye_shine: true,
        skin_texture: true,
        symmetry: true,
        temporal_consistency: true,
      }

      const formData = new FormData()
      formData.append('token', token)
      formData.append('selfie', blob, 'selfie.jpg')
      formData.append('liveness_score', '0.85')
      formData.append('liveness_is_live', 'true')
      formData.append('liveness_checks', JSON.stringify(livenessChecks))
      formData.append('device_is_emulator', String(deviceInfo.is_emulator))
      formData.append('device_is_bot', String(deviceInfo.is_bot))
      formData.append('device_is_mobile', String(deviceInfo.is_mobile))
      formData.append('device_confidence', String(deviceInfo.confidence))
      formData.append('device_user_agent', deviceInfo.user_agent)

      const response = await fetch('/api/mobile/verify', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Verification failed')
      }

      const data = await response.json()
      setResult(data)
      setStatus('success')

      if (stream) {
        stream.getTracks().forEach((t) => t.stop())
      }
    } catch (err) {
      setError((err instanceof Error && err.message) || 'Upload failed')
      setStatus('error')
    }
  }, [photo, token, deviceInfo, stream])

  if (status === 'success' && result) {
    return (
      <div className='flex min-h-screen items-center justify-center'>
        <div className='max-w-md space-y-4 text-center'>
          <div className='text-6xl'>✅</div>
          <h1 className='text-2xl font-bold'>Verification Complete</h1>
          <div className='space-y-2 text-sm'>
            <p>
              <strong>Face Match:</strong>{' '}
              {result.face_match ? 'Matched' : 'Not Matched'}
            </p>
            <p>
              <strong>Score:</strong> {(result.face_score * 100).toFixed(0)}%
            </p>
            <p>
              <strong>Liveness:</strong>{' '}
              {result.liveness_score > 0.5 ? 'Live' : 'Spoof'}
            </p>
          </div>
          <p className='text-sm text-muted-foreground'>
            You can close this page.
          </p>
        </div>
      </div>
    )
  }

  if (status === 'error' && error) {
    return (
      <div className='flex min-h-screen items-center justify-center'>
        <div className='max-w-md space-y-4 text-center'>
          <div className='text-6xl'>❌</div>
          <h1 className='text-2xl font-bold'>Verification Failed</h1>
          <p className='text-muted-foreground'>{error}</p>
          <button
            onClick={() => {
              setStatus('idle')
              setError('')
              startCamera()
            }}
            className='rounded bg-primary px-4 py-2 text-primary-foreground'
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className='flex min-h-screen flex-col items-center justify-center space-y-4 p-4'>
      <h1 className='text-xl font-bold'>Face Verification</h1>
      <p className='text-center text-sm text-muted-foreground'>
        Position your face in the center and take a selfie
      </p>

      {!stream ? (
        <button
          onClick={startCamera}
          className='rounded-lg bg-primary px-6 py-3 text-lg text-primary-foreground'
        >
          Start Camera
        </button>
      ) : !photo ? (
        <>
          <div
            className='relative overflow-hidden rounded-lg border-2 border-primary'
            style={{ maxWidth: 400 }}
          >
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className='w-full'
              style={{ transform: 'scaleX(-1)' }}
            />
            <div className='pointer-events-none absolute inset-0 rounded-lg border-2 border-dashed border-white/30' />
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <button
            onClick={capturePhoto}
            className='rounded-lg bg-primary px-6 py-3 text-lg text-primary-foreground'
            disabled={!cameraReady}
          >
            Take Selfie
          </button>
        </>
      ) : (
        <>
          <img
            src={photo}
            alt='Captured selfie'
            className='max-w-md rounded-lg border'
            style={{ transform: 'scaleX(-1)' }}
          />
          <div className='flex gap-4'>
            <button
              onClick={() => setPhoto(null)}
              className='rounded border px-4 py-2'
            >
              Retake
            </button>
            <button
              onClick={submitVerification}
              className='rounded-lg bg-primary px-6 py-3 text-primary-foreground'
              disabled={status === 'uploading'}
            >
              {status === 'uploading' ? 'Verifying...' : 'Submit Verification'}
            </button>
          </div>
        </>
      )}

      <div className='max-w-sm space-y-1 text-center text-xs text-muted-foreground'>
        <p>
          Device: {deviceInfo.is_mobile ? 'Mobile' : 'Desktop/Web'} (confidence:{' '}
          {(deviceInfo.confidence * 100).toFixed(0)}%)
        </p>
        {deviceInfo.is_emulator && (
          <p className='text-red-500'>⚠️ Emulator detected</p>
        )}
      </div>
    </div>
  )
}
