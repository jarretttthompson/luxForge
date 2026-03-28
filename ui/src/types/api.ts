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

export interface SystemHealth {
  status: string
  engine_running: boolean
  fps: number
  tick_count: number
  active_console: string
  active_scene: string | null
}

export interface AudioDeviceInfo {
  index: number
  name: string
  channels: number
  sample_rate: number
}

export interface AudioConfig {
  device_index: number | null
  sample_rate: number
  buffer_size: number
  simulator_enabled: boolean
  simulator_mode: string
  simulator_bpm: number
}

export interface ProtocolStatusRow {
  name: string
  connected: boolean
  dry_run: boolean
  messages_sent: number
}
