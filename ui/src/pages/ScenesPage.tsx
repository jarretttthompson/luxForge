import { useState } from 'react'

import { SceneEditor } from '../components/scenes/SceneEditor'
import { SceneList } from '../components/scenes/SceneList'
import { useSceneStore } from '../stores/sceneStore'
import type { Scene } from '../types/api'

export function ScenesPage() {
  const scenes = useSceneStore((s) => s.scenes)
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined)
  const [isCreating, setIsCreating] = useState(false)

  const selectedScene = scenes.find((s) => s.id === selectedId)
  const editorOpen = isCreating || selectedId !== undefined

  function handleNew() {
    setSelectedId(undefined)
    setIsCreating(true)
  }

  function handleSelect(id: string) {
    setIsCreating(false)
    setSelectedId(id)
  }

  function handleClose() {
    setIsCreating(false)
    setSelectedId(undefined)
  }

  function handleSaved(scene: Scene) {
    setIsCreating(false)
    setSelectedId(scene.id)
  }

  return (
    <section className="rounded-3xl border border-gray-800 bg-gray-900/70 shadow-2xl shadow-black/20 overflow-hidden">
      <div className="border-b border-gray-800 px-8 py-6">
        <h2 className="text-3xl font-semibold text-gray-100">Scenes</h2>
        <p className="mt-1 text-sm text-gray-400">
          Group mapping rules into named scenes and switch between them during a show.
        </p>
      </div>

      <div className="flex min-h-[540px]">
        {/* List panel */}
        <div
          className={[
            'flex-shrink-0 border-r border-gray-800 transition-all',
            editorOpen ? 'w-72 lg:w-80' : 'w-full',
            editorOpen ? 'hidden sm:flex sm:flex-col' : 'flex flex-col',
          ].join(' ')}
        >
          <SceneList
            selectedId={selectedId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </div>

        {/* Editor panel */}
        {editorOpen && (
          <div className="flex flex-1 flex-col min-w-0">
            <SceneEditor
              key={selectedId ?? 'new'}
              scene={selectedScene}
              onClose={handleClose}
              onSaved={handleSaved}
            />
          </div>
        )}

        {/* Empty state */}
        {!editorOpen && (
          <div className="hidden lg:flex flex-1 items-center justify-center border-l border-gray-800 py-16 text-center">
            <p className="text-sm text-gray-500">Select a scene to edit, or create a new one.</p>
          </div>
        )}
      </div>
    </section>
  )
}
