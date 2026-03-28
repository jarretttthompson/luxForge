import { useEffect } from 'react'
import useReactWebSocket, { ReadyState } from 'react-use-websocket'

import { useAudioStore } from '../stores/audioStore'
import type { AudioAnalysis } from '../types/api'

interface WebSocketPayload {
  audio?: AudioAnalysis
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
    if (!lastJsonMessage?.audio) {
      return
    }

    setAnalysis(lastJsonMessage.audio)
  }, [lastJsonMessage, setAnalysis])

  return {
    isConnected: readyState === ReadyState.OPEN,
    readyState,
  }
}
