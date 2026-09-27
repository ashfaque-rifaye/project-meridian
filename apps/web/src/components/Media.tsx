import { useEffect, useState } from 'react'

/** Monochrome alternates generated for the black & white theme. */
const MONO: Record<string, string> = {
  'hero-convergence': 'mono-architecture',
  'env-layers': 'mono-layers',
  'silent-failure': 'mono-ribbon',
}

export function useTheme() {
  const read = () => document.documentElement.dataset.theme || 'neon'
  const [theme, setTheme] = useState(read)
  useEffect(() => {
    const obs = new MutationObserver(() => setTheme(read()))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => obs.disconnect()
  }, [])
  return theme
}

/**
 * Ambient loop generated with Google Flow (Veo 3.1) and stored in apps/web/public/media.
 * In the B/W theme a monochrome alternate is used when one exists.
 * If a file is missing the element hides itself and the aurora / 3D layer shows through.
 */
export function AmbientVideo({ name, className = '' }: { name: string; className?: string }) {
  const theme = useTheme()
  const preferred = theme === 'mono' && MONO[name] ? MONO[name] : name
  const [src, setSrc] = useState(preferred)
  const [hidden, setHidden] = useState(false)
  useEffect(() => {
    setSrc(preferred)
    setHidden(false)
  }, [preferred])
  if (hidden) return null
  return (
    <video key={src} className={className} src={`/media/${src}.mp4`} autoPlay muted loop playsInline preload="auto"
      onError={() => (src !== name ? setSrc(name) : setHidden(true))} />
  )
}

export function PageBanner({ video, children }: { video: string; children: React.ReactNode }) {
  return (
    <div className="page-bg">
      <div className="page-bg-fallback" />
      <AmbientVideo name={video} />
      {children}
    </div>
  )
}
