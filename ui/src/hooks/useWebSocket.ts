import { useEffect } from 'react'
import useReactWebSocket, { ReadyState } from 'react-use-websocket'

import { useAudioStore } from '../stores/audioStore'
import { useEngineStore } from '../stores/engineStore'
import type { AudioAnalysis } from '../types/api'

interface WebSocketPayload {
  audio?: AudioAnalysis
  outputs?: { target: string; value: number }[]
  engine?: { running: boolean; fps: number; tick_count: number }
  console?: string
  scene?: string | null
  protocols?: Record<string, { connected: boolean; dry_run: boolean; messages_sent: number }>
}

const SOCKET_URL = 'ws://localhost:8765/ws'

function getConnectionState(readyState: ReadyState) {
  switch (readyState) {
    case ReadyState.OPEN:
      return 'open' as const
    case ReadyState.CLOSING:
    case ReadyState.CLOSED:
    case ReadyState.UNINSTANTIATED:
      return 'closed' as const
    default:
      return 'connecting' as const
  }
}

export function useWebSocket() {
  const setAnalysis = useAudioStore((state) => state.setAnalysis)
  const setConnectionState = useAudioStore((state) => state.setConnectionState)
  const applyWsPayload = useEngineStore((state) => state.applyWsPayload)

  const { lastJsonMessage, readyState } = useReactWebSocket<WebSocketPayload>(SOCKET_URL, {
    share: true,
    shouldReconnect: () => true,
    reconnectAttempts: Infinity,
    reconnectInterval: 3000,
  })

  useEffect(() => {
    setConnectionState(getConnectionState(readyState))
  }, [readyState, setConnectionState])

  useEffect(() => {
    if (!lastJsonMessage) {
      return
    }

    if (lastJsonMessage.audio) {
      setAnalysis(lastJsonMessage.audio)
    }

    applyWsPayload({
      outputs: lastJsonMessage.outputs,
      engine: lastJsonMessage.engine,
      console: lastJsonMessage.console,
      scene: lastJsonMessage.scene,
      protocols: lastJsonMessage.protocols,
    })
  }, [lastJsonMessage, setAnalysis, applyWsPayload])

  return {
    isConnected: readyState === ReadyState.OPEN,
    readyState,
  }
}
