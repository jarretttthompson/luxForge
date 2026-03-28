import { useEffect } from 'react'

import { useSceneStore } from '../../stores/sceneStore'
import type { Scene } from '../../types/api'

interface Props {
  selectedId?: string
  onSelect: (id: string) => void
  onNew: () => void
}

function SceneCard({
  scene,
  selected,
  onClick,
  onDelete,
}: {
  scene: Scene
  selected: boolean
  onClick: () => void
  onDelete: () => void
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
          ? 'border-violet-600/60 bg-violet-950/30 ring-1 ring-violet-600/30'
          : 'border-gray-800 bg-gray-900/50 hover:border-gray-700 hover:bg-gray-800/50',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium text-gray-100">{scene.name}</span>
            {scene.active && (
              <span className="flex-shrink-0 rounded-full bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-300">
                active
              </span>
            )}
          </div>
          {scene.description && (
            <p className="mt-0.5 truncate text-xs text-gray-500">{scene.description}</p>
          )}
          <p className="mt-1 text-xs text-gray-600">
            {scene.mapping_rule_ids.length} rule{scene.mapping_rule_ids.length !== 1 ? 's' : ''}
            {scene.transition_time_ms > 0 && ` · ${scene.transition_time_ms}ms fade`}
          </p>
        </div>

        <div className="flex flex-shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            title="Delete scene"
            className="rounded-md p-1 text-gray-500 hover:bg-red-500/15 hover:text-red-400 transition-colors"
          >
            🗑
          </button>
        </div>
      </div>
    </div>
  )
}

export function SceneList({ selectedId, onSelect, onNew }: Props) {
  const scenes = useSceneStore((s) => s.scenes)
  const isLoading = useSceneStore((s) => s.isLoading)
  const error = useSceneStore((s) => s.error)
  const fetchScenes = useSceneStore((s) => s.fetchScenes)
  const deleteScene = useSceneStore((s) => s.deleteScene)

  useEffect(() => { fetchScenes() }, [fetchScenes])

  async function handleDelete(scene: Scene) {
    if (!confirm(`Delete scene "${scene.name}"?`)) return
    await deleteScene(scene.id)
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div>
          <h3 className="text-base font-semibold text-gray-100">Scenes</h3>
          {!isLoading && (
            <p className="text-xs text-gray-500 mt-0.5">
              {scenes.length} {scenes.length === 1 ? 'scene' : 'scenes'}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onNew}
          className="rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
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
        {!isLoading && !error && scenes.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <p className="text-sm text-gray-500">No scenes yet.</p>
            <button
              type="button"
              onClick={onNew}
              className="rounded-lg border border-dashed border-gray-700 px-4 py-2 text-xs text-gray-500 hover:border-gray-500 hover:text-gray-300 transition-colors"
            >
              Create your first scene
            </button>
          </div>
        )}
        {scenes.map((scene) => (
          <SceneCard
            key={scene.id}
            scene={scene}
            selected={scene.id === selectedId}
            onClick={() => onSelect(scene.id)}
            onDelete={() => handleDelete(scene)}
          />
        ))}
      </div>
    </div>
  )
}
