import { create } from 'zustand'

export interface MappingOutput {
  target: string
  value: number
}

export interface EngineStats {
  running: boolean
  fps: number
  tick_count: number
}

export interface ProtocolSnapshot {
  connected: boolean
  dry_run: boolean
  messages_sent: number
}

export interface WsEnginePayload {
  outputs?: MappingOutput[]
  engine?: EngineStats
  console?: string
  scene?: string | null
  protocols?: Record<string, ProtocolSnapshot>
}

interface EngineStoreState {
  outputs: MappingOutput[]
  engine: EngineStats | null
  consoleName: string
  sceneName: string | null
  protocols: Record<string, ProtocolSnapshot>
  applyWsPayload: (payload: WsEnginePayload) => void
}

const initialEngine: EngineStats | null = null

export const useEngineStore = create<EngineStoreState>((set) => ({
  outputs: [],
  engine: initialEngine,
  consoleName: 'none',
  sceneName: null,
  protocols: {},
  applyWsPayload: (payload) =>
    set((state) => ({
      outputs: payload.outputs !== undefined ? payload.outputs : state.outputs,
      engine: payload.engine !== undefined ? payload.engine : state.engine,
      consoleName: payload.console !== undefined ? payload.console : state.consoleName,
      sceneName: payload.scene !== undefined ? payload.scene : state.sceneName,
      protocols: payload.protocols !== undefined ? payload.protocols : state.protocols,
    })),
}))
