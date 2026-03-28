import { useEffect } from 'react'

import { useMappingStore } from '../../stores/mappingStore'
import type { MappingRule } from '../../types/api'

interface Props {
  selectedId?: string
  onSelect: (id: string) => void
  onNew: () => void
}

function RuleCard({
  rule,
  selected,
  onClick,
  onDelete,
  onToggle,
}: {
  rule: MappingRule
  selected: boolean
  onClick: () => void
  onDelete: () => void
  onToggle: () => void
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      className={[
        'group relative rounded-xl border px-4 py-3 cursor-pointer select-none transition-colors',
        selected
          ? 'border-cyan-600/60 bg-cyan-950/40 ring-1 ring-cyan-600/30'
          : 'border-gray-800 bg-gray-900/50 hover:border-gray-700 hover:bg-gray-800/50',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-2 min-w-0">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium text-gray-100">{rule.name}</span>
            {rule.enabled ? (
              <span className="flex-shrink-0 rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                on
              </span>
            ) : (
              <span className="flex-shrink-0 rounded-full bg-gray-700/50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                off
              </span>
            )}
          </div>
          <p className="mt-1 flex items-center gap-1.5 text-xs text-gray-500 truncate">
            <span className="text-cyan-400/80 truncate">{rule.input_param}</span>
            <span>→</span>
            <span className="text-violet-400/80 truncate">{rule.output_param}</span>
          </p>
          {rule.transform_chain.length > 0 && (
            <p className="mt-1 text-xs text-gray-600">
              {rule.transform_chain.length} transform{rule.transform_chain.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        <div className="flex flex-shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onToggle() }}
            title={rule.enabled ? 'Disable' : 'Enable'}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-700/60 hover:text-gray-300 transition-colors"
          >
            {rule.enabled ? '⏸' : '▶'}
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            title="Delete rule"
            className="rounded-md p-1 text-gray-500 hover:bg-red-500/15 hover:text-red-400 transition-colors"
          >
            🗑
          </button>
        </div>
      </div>
    </div>
  )
}

export function MappingList({ selectedId, onSelect, onNew }: Props) {
  const rules = useMappingStore((s) => s.rules)
  const isLoading = useMappingStore((s) => s.isLoading)
  const error = useMappingStore((s) => s.error)
  const fetchRules = useMappingStore((s) => s.fetchRules)
  const deleteRule = useMappingStore((s) => s.deleteRule)
  const updateRule = useMappingStore((s) => s.updateRule)

  useEffect(() => { fetchRules() }, [fetchRules])

  async function handleDelete(rule: MappingRule) {
    if (!confirm(`Delete rule "${rule.name}"?`)) return
    await deleteRule(rule.id)
  }

  async function handleToggle(rule: MappingRule) {
    await updateRule(rule.id, { enabled: !rule.enabled })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div>
          <h3 className="text-base font-semibold text-gray-100">Rules</h3>
          {!isLoading && (
            <p className="text-xs text-gray-500 mt-0.5">
              {rules.length} {rules.length === 1 ? 'rule' : 'rules'}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onNew}
          className="rounded-lg bg-cyan-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-cyan-500 transition-colors"
        >
          + New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
        {isLoading && (
          <div className="flex items-center justify-center py-12 text-sm text-gray-500">
            Loading…
          </div>
        )}
        {error && !isLoading && (
          <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400">
            {error}
          </p>
        )}
        {!isLoading && !error && rules.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <p className="text-sm text-gray-500">No mapping rules yet.</p>
            <button
              type="button"
              onClick={onNew}
              className="rounded-lg border border-dashed border-gray-700 px-4 py-2 text-xs text-gray-500 hover:border-gray-500 hover:text-gray-300 transition-colors"
            >
              Create your first rule
            </button>
          </div>
        )}
        {rules.map((rule) => (
          <RuleCard
            key={rule.id}
            rule={rule}
            selected={rule.id === selectedId}
            onClick={() => onSelect(rule.id)}
            onDelete={() => handleDelete(rule)}
            onToggle={() => handleToggle(rule)}
          />
        ))}
      </div>
    </div>
  )
}
