import { create } from 'zustand'

import type { MappingRule, MappingRuleInput } from '../types/api'

async function requestJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    throw new Error(`Mapping request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

interface MappingStoreState {
  rules: MappingRule[]
  isLoading: boolean
  error: string | null
  fetchRules: () => Promise<void>
  createRule: (rule: MappingRuleInput) => Promise<MappingRule>
  updateRule: (id: string, updates: Partial<MappingRuleInput>) => Promise<MappingRule>
  deleteRule: (id: string) => Promise<void>
}

export const useMappingStore = create<MappingStoreState>((set, get) => ({
  rules: [],
  isLoading: false,
  error: null,
  fetchRules: async () => {
    set({ isLoading: true, error: null })

    try {
      const data = await requestJson<{ rules: MappingRule[] }>('/api/mappings')
      set({ rules: data.rules, isLoading: false })
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Unable to load mappings.',
      })
    }
  },
  createRule: async (rule) => {
    const createdRule = await requestJson<MappingRule>('/api/mappings', {
      method: 'POST',
      body: JSON.stringify({
        ...rule,
        transform_chain: rule.transform_chain ?? [],
        enabled: rule.enabled ?? true,
      }),
    })

    set((state) => ({ rules: [...state.rules, createdRule] }))
    return createdRule
  },
  updateRule: async (id, updates) => {
    const updatedRule = await requestJson<MappingRule>(`/api/mappings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })

    set((state) => ({
      rules: state.rules.map((rule) => (rule.id === id ? updatedRule : rule)),
    }))
    return updatedRule
  },
  deleteRule: async (id) => {
    await requestJson<void>(`/api/mappings/${id}`, { method: 'DELETE' })
    set({
      rules: get().rules.filter((rule) => rule.id !== id),
    })
  },
}))
