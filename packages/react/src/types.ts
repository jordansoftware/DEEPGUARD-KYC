export interface DeepGuardConfig {
  apiUrl: string
  apiKey?: string
}

export interface AnalysisResult {
  score: number
  verdict: 'authentique' | 'suspect' | 'forge'
  verdict_label: string
  heatmap: string
  image: string
  signals: {
    mela: { score: number; note: string }
    noise: { score: number; note: string }
    ela: { score: number; note: string }
    meta: { score: number; notes: string[] }
  }
  reasons: string[]
}

export interface FaceMatchResult {
  match: boolean
  distance: number
  model: string
  threshold: number
}

export interface LivenessResult {
  is_live: boolean
  score: number
  checks: Record<string, unknown>
}
