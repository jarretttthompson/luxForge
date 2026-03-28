import { useEffect, useState } from 'react'

import { useMappingStore } from '../../stores/mappingStore'
import type { MappingRule } from '../../types/api'
import { ParameterPicker } from './ParameterPicker'
import type { ParameterInfo } from './ParameterPicker'

// ── Transform schema ──────────────────────────────────────────────────────────

interface ParamSchema {
  key: string
  label: string
  default: number
  min?: number
  step?: number
}

const TRANSFORM_SCHEMAS: Record<string, ParamSchema[]> = {
  Smooth: [
    { key: 'attack', label: 'Attack (s)', default: 0.1, min: 0, step: 0.01 },
    { key: 'release', label: 'Release (s)', default: 0.4, min: 0, step: 0.01 },
  ],
  Scale: [
    { key: 'min_out', label: 'Min out', default: 0, step: 0.01 },
    { key: 'max_out', label: 'Max out', default: 1, step: 0.01 },
  ],
  Threshold: [
    { key: 'level', label: 'Level', default: 0.5, min: 0, step: 0.01 },
    { key: 'above_val', label: 'Above value', default: 1, step: 0.01 },
    { key: 'below_val', label: 'Below value', default: 0, step: 0.01 },
  ],
  Curve: [{ key: 'exponent', label: 'Exponent', default: 2, min: 0.01, step: 0.1 }],
  Invert: [],
  Pulse: [{ key: 'duration_ms', label: 'Duration (ms)', default: 100, min: 1, step: 1 }],
  MapRange: [
    { key: 'in_lo', label: 'In lo', default: 0, step: 0.01 },
    { key: 'in_hi', label: 'In hi', default: 1, step: 0.01 },
    { key: 'out_lo', label: 'Out lo', default: 0, step: 0.01 },
    { key: 'out_hi', label: 'Out hi', default: 1, step: 0.01 },
  ],
  Clamp: [
    { key: 'lo', label: 'Lo', default: 0, step: 0.01 },
    { key: 'hi', label: 'Hi', default: 1, step: 0.01 },
  ],
}

const TRANSFORM_TYPES = Object.keys(TRANSFORM_SCHEMAS)

function defaultParams(type: string): Record<string, number> {
  const schema = TRANSFORM_SCHEMAS[type] ?? []
  return Object.fromEntries(schema.map((p) => [p.key, p.default]))
}

// ── Transform chain subcomponents ─────────────────────────────────────────────

function transformLabel(t: Record<string, unknown>): string {
  const schema = TRANSFORM_SCHEMAS[t.type as string] ?? []
  const parts = schema.map((p) => {
    const v = t[p.key]
    return `${p.key}=${typeof v === 'number' ? v : '?'}`
  })
  return parts.length > 0 ? parts.join('  ') : '—'
}

interface ChainEditorProps {
  chain: Record<string, unknown>[]
  onChange: (chain: Record<string, unknown>[]) => void
}

function TransformChainEditor({ chain, onChange }: ChainEditorProps) {
  const [addOpen, setAddOpen] = useState(false)
  const [newType, setNewType] = useState('Smooth')
  const [newParams, setNewParams] = useState<Record<string, number>>(defaultParams('Smooth'))

  function handleTypeChange(type: string) {
    setNewType(type)
    setNewParams(defaultParams(type))
  }

  function handleAdd() {
    onChange([...chain, { type: newType, ...newParams }])
    setAddOpen(false)
    setNewType('Smooth')
    setNewParams(defaultParams('Smooth'))
  }

  function handleRemove(index: number) {
    onChange(chain.filter((_, i) => i !== index))
  }

  const schema = TRANSFORM_SCHEMAS[newType] ?? []

  return (
    <div className="space-y-2">
      {chain.length === 0 && (
        <p className="text-xs text-gray-500 italic">No transforms — input passes through unchanged.</p>
      )}
      {chain.map((t, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-800/70 px-3 py-2"
        >
          <div className="min-w-0 flex-1">
            <span className="rounded-md bg-cyan-900/50 px-1.5 py-0.5 text-xs font-semibold text-cyan-300">
              {t.type as string}
            </span>
            <span className="ml-2 text-xs text-gray-400">{transformLabel(t)}</span>
          </div>
          <button
            type="button"
            onClick={() => handleRemove(i)}
            className="ml-2 flex-shrink-0 rounded p-1 text-gray-500 hover:bg-red-500/15 hover:text-red-400 transition-colors"
            aria-label={`Remove transform ${i + 1}`}
          >
            ✕
          </button>
        </div>
      ))}

      {addOpen ? (
        <div className="rounded-lg border border-cyan-700/40 bg-cyan-950/30 p-3 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Type</label>
            <select
              value={newType}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
            >
              {TRANSFORM_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          {schema.length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {schema.map((p) => (
                <div key={p.key}>
                  <label className="block text-xs font-medium text-gray-400 mb-1">{p.label}</label>
                  <input
                    type="number"
                    value={newParams[p.key] ?? p.default}
                    min={p.min}
                    step={p.step}
                    onChange={(e) =>
                      setNewParams((prev) => ({ ...prev, [p.key]: parseFloat(e.target.value) || 0 }))
                    }
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-gray-100 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
                  />
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleAdd}
              className="rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-cyan-500 transition-colors"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => setAddOpen(false)}
              className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="mt-1 w-full rounded-lg border border-dashed border-gray-700 py-2 text-xs font-medium text-gray-500 hover:border-gray-500 hover:text-gray-300 transition-colors"
        >
          + Add transform
        </button>
      )}
    </div>
  )
}

// ── MappingEditor ─────────────────────────────────────────────────────────────

interface Props {
  rule?: MappingRule
  onClose: () => void
  onSaved: (rule: MappingRule) => void
}

interface ParameterLists {
  inputs: ParameterInfo[]
  outputs: ParameterInfo[]
}

export function MappingEditor({ rule, onClose, onSaved }: Props) {
  const createRule = useMappingStore((s) => s.createRule)
  const updateRule = useMappingStore((s) => s.updateRule)

  const isEditing = Boolean(rule)

  const [name, setName] = useState(rule?.name ?? '')
  const [inputParam, setInputParam] = useState(rule?.input_param ?? '')
  const [outputParam, setOutputParam] = useState(rule?.output_param ?? '')
  const [enabled, setEnabled] = useState(rule?.enabled ?? true)
  const [chain, setChain] = useState<Record<string, unknown>[]>(rule?.transform_chain ?? [])
  const [params, setParams] = useState<ParameterLists>({ inputs: [], outputs: [] })
  const [paramsLoading, setParamsLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setParamsLoading(true)
    fetch('/api/mappings/parameters/list')
      .then((r) => r.json() as Promise<ParameterLists>)
      .then((data) => { setParams(data); setParamsLoading(false) })
      .catch(() => setParamsLoading(false))
  }, [])

  // Reset form when rule prop changes (navigating between rules)
  useEffect(() => {
    setName(rule?.name ?? '')
    setInputParam(rule?.input_param ?? '')
    setOutputParam(rule?.output_param ?? '')
    setEnabled(rule?.enabled ?? true)
    setChain(rule?.transform_chain ?? [])
    setError(null)
  }, [rule])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required.'); return }
    if (!inputParam) { setError('Input parameter is required.'); return }
    if (!outputParam) { setError('Output parameter is required.'); return }

    setSaving(true)
    setError(null)
    try {
      let saved: MappingRule
      if (isEditing && rule) {
        saved = await updateRule(rule.id, {
          name: name.trim(),
          input_param: inputParam,
          output_param: outputParam,
          enabled,
          transform_chain: chain,
        })
      } else {
        saved = await createRule({
          name: name.trim(),
          input_param: inputParam,
          output_param: outputParam,
          enabled,
          transform_chain: chain,
        })
      }
      onSaved(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <h3 className="text-base font-semibold text-gray-100">
          {isEditing ? 'Edit rule' : 'New rule'}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-800 hover:text-gray-300 transition-colors"
          aria-label="Close editor"
        >
          ✕
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-y-auto px-6 py-5 gap-5">
        {/* Name */}
        <div>
          <label htmlFor="rule-name" className="block text-xs font-medium text-gray-400 mb-1">
            Name
          </label>
          <input
            id="rule-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Sub bass → fader 1"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
          />
        </div>

        {/* Input param */}
        <div>
          <label htmlFor="rule-input" className="block text-xs font-medium text-gray-400 mb-1">
            Input parameter
          </label>
          <ParameterPicker
            id="rule-input"
            value={inputParam}
            onChange={setInputParam}
            params={params.inputs}
            isLoading={paramsLoading}
            placeholder="Select audio input…"
          />
        </div>

        {/* Output param */}
        <div>
          <label htmlFor="rule-output" className="block text-xs font-medium text-gray-400 mb-1">
            Output parameter
          </label>
          <ParameterPicker
            id="rule-output"
            value={outputParam}
            onChange={setOutputParam}
            params={params.outputs}
            isLoading={paramsLoading}
            placeholder="Select console output…"
          />
        </div>

        {/* Enabled toggle */}
        <div className="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-800/60 px-4 py-3">
          <span className="text-sm text-gray-300">Enabled</span>
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            onClick={() => setEnabled((v) => !v)}
            className={[
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200',
              enabled ? 'bg-cyan-600' : 'bg-gray-700',
            ].join(' ')}
          >
            <span
              className={[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200',
                enabled ? 'translate-x-5' : 'translate-x-0',
              ].join(' ')}
            />
          </button>
        </div>

        {/* Transform chain */}
        <div>
          <p className="mb-2 text-xs font-medium text-gray-400">Transform chain</p>
          <TransformChainEditor chain={chain} onChange={setChain} />
        </div>

        {/* Error */}
        {error && (
          <p className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400 border border-red-500/20">
            {error}
          </p>
        )}

        {/* Actions */}
        <div className="mt-auto flex gap-3 pt-2 pb-1">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 rounded-lg bg-cyan-600 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : isEditing ? 'Save changes' : 'Create rule'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
