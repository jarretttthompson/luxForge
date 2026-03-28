export interface AudioBands {
  sub: number
  low: number
  mid: number
  hi_mid: number
  high: number
}

export interface AudioAnalysis {
  fft: number[]
  bands: AudioBands
  rms: number
  peak: number
  bpm: number
  beat: boolean
  beat_phase: number
  onset: boolean
  spectral_centroid: number
}

export interface MappingRule {
  id: string
  name: string
  input_param: string
  output_param: string
  transform_chain: Record<string, unknown>[]
  condition: string | null
  enabled: boolean
}

export interface Scene {
  id: string
  name: string
  description: string
  mapping_rule_ids: string[]
  transition_time_ms: number
  active: boolean
}

export interface MappingRuleInput {
  name: string
  input_param: string
  output_param: string
  transform_chain?: Record<string, unknown>[]
  condition?: string | null
  enabled?: boolean
}

export interface SceneInput {
  name: string
  description?: string
  mapping_rule_ids?: string[]
  transition_time_ms?: number
}
