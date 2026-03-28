import { create } from 'zustand'

import type { Scene, SceneInput } from '../types/api'

async function requestJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    throw new Error(`Scene request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

interface SceneStoreState {
  scenes: Scene[]
  isLoading: boolean
  error: string | null
  fetchScenes: () => Promise<void>
  createScene: (scene: SceneInput) => Promise<Scene>
  updateScene: (id: string, updates: Partial<SceneInput>) => Promise<Scene>
  deleteScene: (id: string) => Promise<void>
}

export const useSceneStore = create<SceneStoreState>((set, get) => ({
  scenes: [],
  isLoading: false,
  error: null,
  fetchScenes: async () => {
    set({ isLoading: true, error: null })

    try {
      const data = await requestJson<{ scenes: Scene[] }>('/api/scenes')
      set({ scenes: data.scenes, isLoading: false })
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Unable to load scenes.',
      })
    }
  },
  createScene: async (scene) => {
    const createdScene = await requestJson<Scene>('/api/scenes', {
      method: 'POST',
      body: JSON.stringify({
        description: '',
        mapping_rule_ids: [],
        transition_time_ms: 0,
        ...scene,
      }),
    })

    set((state) => ({ scenes: [...state.scenes, createdScene] }))
    return createdScene
  },
  updateScene: async (id, updates) => {
    const updatedScene = await requestJson<Scene>(`/api/scenes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })

    set((state) => ({
      scenes: state.scenes.map((scene) => (scene.id === id ? updatedScene : scene)),
    }))
    return updatedScene
  },
  deleteScene: async (id) => {
    await requestJson<void>(`/api/scenes/${id}`, { method: 'DELETE' })
    set({
      scenes: get().scenes.filter((scene) => scene.id !== id),
    })
  },
}))
