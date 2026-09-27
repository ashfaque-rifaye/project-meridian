import { useState } from 'react'
import type { Go } from '../App'
import { Icon } from '../components/ui'

export default function PitchDeck({ go }: { go: Go }) {
  const [fullscreen, setFullscreen] = useState(false)

  const openExternal = () => {
    window.open('/slides.html', '_blank')
  }

  return (
    <div className="page" style={{ padding: '20px 28px', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '0.72rem', color: 'var(--accent, #00e5ff)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
            IBM BOB 2.0 HACKATHON · EXECUTIVE BRIEFING
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>
            Meridian Project <span style={{ color: '#00e5ff' }}>Pitch Deck</span>
          </h1>
          <p style={{ color: '#8e9bb0', fontSize: '0.85rem', marginTop: '4px', margin: 0 }}>
            Interactive 6-slide presentation covering the problem, the 38-hour silent failure, noise filtering, the 5-stage engine, IBM Bob integration, and verifiable ROI.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn ghost sm" onClick={openExternal} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Icon name="external" size={14} /> Open in New Tab
          </button>
          <a href="/slides.html" target="_blank" download="MERIDIAN_PITCH_DECK.html" className="btn ghost sm" style={{ display: 'flex', alignItems: 'center', gap: '6px', textDecoration: 'none' }}>
            <Icon name="doc" size={14} /> Save Standalone HTML
          </a>
        </div>
      </div>

      <div style={{
        flex: 1,
        borderRadius: '16px',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        background: '#07090e',
        position: 'relative'
      }}>
        <iframe
          src="/slides.html"
          title="Meridian Pitch Deck"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            display: 'block'
          }}
          allow="fullscreen"
        />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.75rem', color: '#64748b', fontFamily: 'var(--font-mono, monospace)' }}>
        <div>
          <span>Shortcuts: </span>
          <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>Space</kbd> / 
          <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>← →</kbd> Next/Prev &nbsp;|&nbsp;
          <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>N</kbd> Speaker Notes &nbsp;|&nbsp;
          <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>O</kbd> Overview Grid &nbsp;|&nbsp;
          <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>F</kbd> Fullscreen
        </div>
        <div>
          <span>Standalone: </span>
          <code style={{ color: '#00e5ff' }}>slides.html</code>
        </div>
      </div>
    </div>
  )
}
