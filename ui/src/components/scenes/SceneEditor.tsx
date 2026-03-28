import { useEffect, useState } from 'react'

import { useMappingStore } from '../../stores/mappingStore'
import { useSceneStore } from '../../stores/sceneStore'
import type { Scene } from '../../types/api'

interface Props {
  scene?: Scene
  onClose: () => void
  onSaved: (scene: Scene) => void
}

export function SceneEditor({ scene, onClose, onSaved }: Props) {
  const createScene = useSceneStore((s) => s.createScene)
  const updateScene = useSceneStore((s) => s.updateScene)
  const rules = useMappingStore((s) => s.rules)
  const fetchRules = useMappingStore((s) => s.fetchRules)

  const isEditing = Boolean(scene)

  const [name, setName] = useState(scene?.name ?? '')
  const [description, setDescription] = useState(scene?.description ?? '')
  const [selectedRuleIds, setSelectedRuleIds] = useState<string[]>(scene?.mapping_rule_ids ?? [])
  const [transitionMs, setTransitionMs] = useState(scene?.transition_time_ms ?? 0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { fetchRules() }, [fetchRules])

  // Sync form when scene prop changes
  useEffect(() => {
    setName(scene?.name ?? '')
    setDescription(scene?.description ?? '')
    setSelectedRuleIds(scene?.mapping_rule_ids ?? [])
    setTransitionMs(scene?.transition_time_ms ?? 0)
    setError(null)
  }, [scene])

  function toggleRule(id: string) {
    setSelectedRuleIds((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id],
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required.'); return }

    setSaving(true)
    setError(null)
    try {
      let saved: Scene
      const payload = {
        name: name.trim(),
        description: description.trim(),
        mapping_rule_ids: selectedRuleIds,
        transition_time_ms: transitionMs,
      }
      if (isEditing && scene) {
        saved = await updateScene(scene.id, payload)
      } else {
        saved = await createScene(payload)
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
          {isEditing ? 'Edit scene' : 'New scene'}
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
          <label htmlFor="scene-name" className="block text-xs font-medium text-gray-400 mb-1">
            Name
          </label>
          <input
            id="scene-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Drop scene"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/30"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="scene-desc" className="block text-xs font-medium text-gray-400 mb-1">
            Description <span className="text-gray-600">(optional)</span>
          </label>
          <textarea
            id="scene-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            placeholder="What does this scene do?"
            className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/30"
          />
        </div>

        {/* Transition time */}
        <div>
          <label htmlFor="scene-fade" className="block text-xs font-medium text-gray-400 mb-1">
            Transition time
            <span className="ml-2 text-gray-500 tabular-nums">
              {transitionMs === 0 ? 'instant' : `${transitionMs} ms`}
            </span>
          </label>
          <input
            id="scene-fade"
            type="range"
            min={0}
            max={2000}
            step={50}
            value={transitionMs}
            onChange={(e) => setTransitionMs(Number(e.target.value))}
            className="w-full accent-violet-500"
          />
          <div className="mt-0.5 flex justify-between text-[10px] text-gray-600">
            <span>Instant</span>
            <span>2 s</span>
          </div>
        </div>

        {/* Mapping rules */}
        <div>
          <p className="mb-2 text-xs font-medium text-gray-400">
            Mapping rules
            {selectedRuleIds.length > 0 && (
              <span className="ml-2 text-gray-500">{selectedRuleIds.length} selected</span>
            )}
          </p>
          {rules.length === 0 ? (
            <p className="text-xs text-gray-600 italic">
              No mapping rules available — create some in the Mapping page.
            </p>
          ) : (
            <div className="max-h-56 overflow-y-auto space-y-1.5 rounded-lg border border-gray-800 bg-gray-900/40 p-2">
              {rules.map((rule) => {
                const checked = selectedRuleIds.includes(rule.id)
                return (
                  <label
                    key={rule.id}
                    className={[
                      'flex cursor-pointer items-start gap-3 rounded-lg px-3 py-2.5 transition-colors',
                      checked ? 'bg-violet-900/25' : 'hover:bg-gray-800/60',
                    ].join(' ')}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleRule(rule.id)}
                      className="mt-0.5 h-4 w-4 flex-shrink-0 accent-violet-500 cursor-pointer"
                    />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-200 truncate">{rule.name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {rule.input_param} → {rule.output_param}
                      </p>
                    </div>
                  </label>
                )
              })}
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400">
            {error}
          </p>
        )}

        {/* Actions */}
        <div className="mt-auto flex gap-3 pt-2 pb-1">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 rounded-lg bg-violet-600 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : isEditing ? 'Save changes' : 'Create scene'}
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
