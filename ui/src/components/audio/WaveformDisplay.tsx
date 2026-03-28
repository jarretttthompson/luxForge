import { useEffect, useRef } from 'react'

import { useAudioStore } from '../../stores/audioStore'

const BUFFER_LEN = 360

/**
 * Scrolling amplitude trace built from RMS/peak (no raw samples in the wire protocol).
 * Reads like a classic level/waveform strip for the dashboard.
 */
export function WaveformDisplay() {
  const lastUpdated = useAudioStore((s) => s.lastUpdated)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const bufferRef = useRef<number[]>(Array.from({ length: BUFFER_LEN }, () => 0))

  useEffect(() => {
    if (lastUpdated == null) return
    const rms = useAudioStore.getState().analysis.rms
    const peak = useAudioStore.getState().analysis.peak
    const v = Math.min(1, Math.max(0, rms * 0.75 + peak * 0.25))
    const buf = bufferRef.current
    buf.shift()
    buf.push(v)
  }, [lastUpdated])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const draw = () => {
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const dpr = window.devicePixelRatio || 1
      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      if (w < 2 || h < 2) return

      canvas.width = Math.floor(w * dpr)
      canvas.height = Math.floor(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      ctx.fillStyle = '#030712'
      ctx.fillRect(0, 0, w, h)

      const buf = bufferRef.current
      const mid = h / 2
      const ampScale = mid * 0.92

      ctx.beginPath()
      ctx.strokeStyle = '#67e8f9'
      ctx.lineWidth = 1.5
      ctx.lineJoin = 'round'

      for (let i = 0; i < buf.length; i++) {
        const x = (i / (buf.length - 1)) * w
        const y = mid - buf[i]! * ampScale
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(0, mid)
      ctx.lineTo(w, mid)
      ctx.strokeStyle = 'rgba(75, 85, 99, 0.5)'
      ctx.lineWidth = 1
      ctx.stroke()

      ctx.beginPath()
      for (let i = 0; i < buf.length; i++) {
        const x = (i / (buf.length - 1)) * w
        const y = mid - buf[i]! * ampScale
        if (i === 0) {
          ctx.moveTo(x, mid)
          ctx.lineTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.lineTo(w, mid)
      ctx.closePath()
      const fill = ctx.createLinearGradient(0, 0, 0, h)
      fill.addColorStop(0, 'rgba(6, 182, 212, 0.22)')
      fill.addColorStop(1, 'rgba(6, 182, 212, 0.02)')
      ctx.fillStyle = fill
      ctx.fill()
    }

    draw()
    const ro = new ResizeObserver(() => draw())
    ro.observe(canvas)
    return () => ro.disconnect()
  }, [lastUpdated])

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium tracking-wide text-gray-300">Level trace</h3>
        <span className="text-xs text-gray-500">RMS + peak</span>
      </div>
      <canvas
        ref={canvasRef}
        className="h-36 w-full rounded-lg bg-gray-950"
        aria-label="Scrolling audio level waveform"
        role="img"
      />
    </div>
  )
}
