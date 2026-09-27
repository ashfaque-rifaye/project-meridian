import { useEffect, useRef } from 'react'
import * as THREE from 'three'

type FlowProps = {
  mode: 'flow'
  components: { id: string; label: string }[]
  edges: { producer: string; consumer: string; state: string }[]
  composition: Record<string, { version?: string } | undefined>
}
type StackProps = {
  mode: 'stack'
  components: { id: string; label: string }[]
  envs: { environment: string; verdict: string; composition: Record<string, string> }[]
  reference: Record<string, string>
}
type Props = (FlowProps | StackProps) & { height?: number; interactive?: boolean }

function cssColor(name: string, fallback: string) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return new THREE.Color(v || fallback)
}

function glowTexture() {
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const g = c.getContext('2d')!
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64)
  grad.addColorStop(0, 'rgba(255,255,255,1)')
  grad.addColorStop(0.25, 'rgba(255,255,255,0.45)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  g.fillStyle = grad
  g.fillRect(0, 0, 128, 128)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

export default function Scene3D(props: Props) {
  const host = useRef<HTMLDivElement>(null)
  const key = JSON.stringify(props.mode === 'flow'
    ? { e: props.edges.map((e) => e.state), c: props.composition }
    : { e: props.envs.map((e) => [e.verdict, e.composition]) })

  useEffect(() => {
    const el = host.current
    if (!el) return
    const width = el.clientWidth
    const height = el.clientHeight
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x04050a, 0.035)
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 200)
    const halfWidth = props.mode === 'flow' ? 9.2 : 9.6
    const fitDistance = (aspect: number) => Math.max(props.mode === 'flow' ? 15 : 17, halfWidth / (Math.tan((42 / 2) * Math.PI / 180) * aspect) + 2)
    camera.position.set(0, 2.2, fitDistance(width / height))

    const OK = cssColor('--ok', '#00f5a0')
    const FAIL = cssColor('--fail', '#ff3d71')
    const ACC = cssColor('--accent', '#22d3ee')
    const VIO = new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--accent-strong').trim() || '#7c3aed')
    const WARN = cssColor('--warn', '#ffd60a')
    const HOLD = cssColor('--hold', '#b388ff')
    const stateColor = (s: string) =>
      s === 'FAILED' ? FAIL : s === 'VERIFIED' ? OK : s === 'VERIFIED_BY_PROBE' ? ACC : s === 'UNTESTED' ? WARN : HOLD

    scene.add(new THREE.AmbientLight(0xffffff, 0.35))
    const key1 = new THREE.PointLight(ACC, 60, 60)
    key1.position.set(-8, 8, 10)
    scene.add(key1)
    const key2 = new THREE.PointLight(VIO, 70, 60)
    key2.position.set(9, -4, 8)
    scene.add(key2)

    const glow = glowTexture()
    const disposables: { dispose: () => void }[] = [glow]
    const world = new THREE.Group()
    scene.add(world)

    // starfield
    const starGeo = new THREE.BufferGeometry()
    const starPos = new Float32Array(900 * 3)
    for (let i = 0; i < 900; i++) {
      starPos[i * 3] = (Math.random() - 0.5) * 80
      starPos[i * 3 + 1] = (Math.random() - 0.5) * 50
      starPos[i * 3 + 2] = (Math.random() - 0.5) * 60 - 10
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3))
    const starMat = new THREE.PointsMaterial({ size: 0.06, color: 0xffffff, transparent: true, opacity: 0.55 })
    const stars = new THREE.Points(starGeo, starMat)
    scene.add(stars)
    disposables.push(starGeo, starMat)

    const labels: { el: HTMLDivElement; pos: THREE.Vector3; below: boolean }[] = []
    const addLabel = (html: string, pos: THREE.Vector3, cls = '', below = false) => {
      const d = document.createElement('div')
      d.className = `lbl ${cls}`
      d.innerHTML = html
      el.appendChild(d)
      labels.push({ el: d, pos, below })
    }
    const sprite = (color: THREE.Color, scale: number, opacity = 0.9) => {
      const m = new THREE.SpriteMaterial({ map: glow, color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false })
      const s = new THREE.Sprite(m)
      s.scale.setScalar(scale)
      disposables.push(m)
      return s
    }

    const animated: ((t: number) => void)[] = []

    if (props.mode === 'flow') {
      const n = props.components.length
      const pos: Record<string, THREE.Vector3> = {}
      props.components.forEach((c, i) => {
        const u = i / (n - 1)
        const x = (u - 0.5) * 15
        const y = Math.sin(u * Math.PI * 2) * 1.6
        const z = Math.cos(u * Math.PI * 1.5) * 2.2 - 1
        pos[c.id] = new THREE.Vector3(x, y, z)
      })
      const bad = new Set(props.edges.filter((e) => e.state === 'FAILED').flatMap((e) => [e.consumer]))

      props.components.forEach((c) => {
        const p = pos[c.id]
        const isBad = bad.has(c.id)
        const color = isBad ? FAIL : ACC
        const shellGeo = new THREE.IcosahedronGeometry(0.62, 1)
        const shellMat = new THREE.MeshPhysicalMaterial({
          color: 0xffffff, metalness: 0.1, roughness: 0.05, transparent: true, opacity: 0.32,
          clearcoat: 1, clearcoatRoughness: 0.05, emissive: color, emissiveIntensity: 0.18, flatShading: true,
        })
        const shell = new THREE.Mesh(shellGeo, shellMat)
        shell.position.copy(p)
        const wire = new THREE.LineSegments(new THREE.EdgesGeometry(shellGeo), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.55 }))
        shell.add(wire)
        const coreGeo = new THREE.SphereGeometry(0.2, 24, 24)
        const coreMat = new THREE.MeshBasicMaterial({ color })
        const core = new THREE.Mesh(coreGeo, coreMat)
        shell.add(core)
        shell.add(sprite(color, isBad ? 3.6 : 2.4, isBad ? 1 : 0.7))
        world.add(shell)
        disposables.push(shellGeo, shellMat, coreGeo, coreMat, wire.geometry, wire.material as THREE.Material)
        const phase = Math.random() * 6
        animated.push((t) => {
          shell.rotation.y = t * 0.4 + phase
          shell.rotation.x = Math.sin(t * 0.3 + phase) * 0.3
          shell.position.y = p.y + Math.sin(t * 0.9 + phase) * 0.12
          if (isBad) coreMat.color.copy(FAIL).multiplyScalar(0.75 + 0.35 * Math.sin(t * 6))
        })
        const v = props.composition[c.id]?.version ?? '—'
        const i = props.components.indexOf(c)
        addLabel(`<b>${c.label}</b> · ${v}`, shell.position, isBad ? 'bad' : '', i % 2 === 1)
      })

      props.edges.forEach((e) => {
        const a = pos[e.producer]
        const b = pos[e.consumer]
        if (!a || !b) return
        const mid = a.clone().lerp(b, 0.5).add(new THREE.Vector3(0, 0.9, 0.6))
        const curve = new THREE.QuadraticBezierCurve3(a, mid, b)
        const color = stateColor(e.state)
        const failed = e.state === 'FAILED'
        const tubeGeo = new THREE.TubeGeometry(curve, 48, failed ? 0.05 : 0.035, 8, false)
        const tubeMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: failed ? 0.9 : 0.45 })
        world.add(new THREE.Mesh(tubeGeo, tubeMat))
        disposables.push(tubeGeo, tubeMat)
        const pulses = Array.from({ length: failed ? 5 : 3 }, (_, i) => {
          const s = sprite(color, failed ? 0.9 : 0.7, 1)
          world.add(s)
          return { s, off: i / (failed ? 5 : 3) }
        })
        animated.push((t) => {
          if (failed) tubeMat.opacity = 0.55 + 0.4 * Math.abs(Math.sin(t * 3))
          pulses.forEach(({ s, off }) => {
            let u = (t * 0.18 + off) % 1
            if (failed && u > 0.55) {
              // the record never arrives intact: pulses scatter past the midpoint
              const k = (u - 0.55) / 0.45
              const p = curve.getPoint(0.55)
              s.position.set(p.x + Math.sin(off * 40) * k * 1.6, p.y - k * 1.8, p.z + Math.cos(off * 40) * k * 1.2)
              ;(s.material as THREE.SpriteMaterial).opacity = 1 - k
              return
            }
            ;(s.material as THREE.SpriteMaterial).opacity = 1
            s.position.copy(curve.getPoint(u))
          })
        })
      })
    } else {
      const envs = props.envs
      const comps = props.components
      const slabY = (i: number) => (i - (envs.length - 1) / 2) * 2.3
      envs.forEach((env, i) => {
        const y = slabY(i)
        const diverged = env.verdict === 'DIVERGED'
        const color = diverged ? FAIL : env.verdict === 'CONVERGED' ? OK : WARN
        const geo = new THREE.BoxGeometry(15, 0.06, 3.4)
        const mat = new THREE.MeshPhysicalMaterial({
          color: 0xffffff, transparent: true, opacity: diverged ? 0.14 : 0.08, roughness: 0.1, metalness: 0.1,
          clearcoat: 1, emissive: color, emissiveIntensity: diverged ? 0.35 : 0.08,
        })
        const slab = new THREE.Mesh(geo, mat)
        slab.position.set(0, y, 0)
        const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color, transparent: true, opacity: diverged ? 0.9 : 0.45 }))
        slab.add(edges)
        world.add(slab)
        disposables.push(geo, mat, edges.geometry, edges.material as THREE.Material)
        addLabel(env.environment.toUpperCase(), new THREE.Vector3(-8.6, y, 0), `env ${diverged ? 'bad' : ''}`)
        comps.forEach((c, j) => {
          const x = (j - (comps.length - 1) / 2) * 1.8
          const version = env.composition[c.id]
          const mismatch = env.environment === 'prod' && version !== props.reference[c.id]
          const col = mismatch ? FAIL : ACC
          const g = new THREE.OctahedronGeometry(mismatch ? 0.26 : 0.18, 0)
          const m = new THREE.MeshBasicMaterial({ color: col })
          const node = new THREE.Mesh(g, m)
          node.position.set(x, y + 0.28, 0)
          node.add(sprite(col, mismatch ? 1.9 : 0.9, mismatch ? 1 : 0.6))
          world.add(node)
          disposables.push(g, m)
          animated.push((t) => {
            node.rotation.y = t * (mismatch ? 2 : 0.8) + j
            if (mismatch) node.position.y = y + 0.32 + Math.sin(t * 4) * 0.08
          })
          if (mismatch) addLabel(`<b>${c.label}</b> ${version} ≠ ${props.reference[c.id]}`, new THREE.Vector3(x, y + 0.9, 0), 'bad', j % 2 === 1)
        })
        animated.push((t) => {
          slab.position.y = y + Math.sin(t * 0.6 + i) * 0.05
          if (diverged) mat.emissiveIntensity = 0.25 + 0.2 * Math.abs(Math.sin(t * 2))
        })
      })
      // promotion beams between layers
      comps.forEach((_, j) => {
        const x = (j - (comps.length - 1) / 2) * 1.8
        const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x, slabY(0), 0), new THREE.Vector3(x, slabY(envs.length - 1), 0)])
        const mat = new THREE.LineDashedMaterial({ color: ACC, dashSize: 0.12, gapSize: 0.12, transparent: true, opacity: 0.35 })
        const line = new THREE.Line(geo, mat)
        line.computeLineDistances()
        world.add(line)
        disposables.push(geo, mat)
      })
      world.rotation.x = 0.35
    }

    // interaction: gentle orbit + mouse parallax
    let mx = 0
    let my = 0
    const onMove = (ev: MouseEvent) => {
      const r = el.getBoundingClientRect()
      mx = ((ev.clientX - r.left) / r.width - 0.5) * 2
      my = ((ev.clientY - r.top) / r.height - 0.5) * 2
    }
    el.addEventListener('mousemove', onMove)

    const clock = new THREE.Clock()
    const v = new THREE.Vector3()
    let raf = 0
    const tick = () => {
      const t = clock.getElapsedTime()
      animated.forEach((f) => f(t))
      const base = props.mode === 'flow' ? Math.sin(t * 0.12) * 0.35 : Math.sin(t * 0.1) * 0.5
      world.rotation.y += ((base + mx * 0.35) - world.rotation.y) * 0.04
      camera.position.y += ((props.mode === 'flow' ? 2.2 : 3) - my * 1.5 - camera.position.y) * 0.04
      camera.lookAt(0, 0, 0)
      stars.rotation.y = t * 0.01
      renderer.render(scene, camera)
      const w = el.clientWidth
      const h = el.clientHeight
      for (const l of labels) {
        v.copy(l.pos)
        l.el.parentElement && l.pos && (() => {
          const worldPos = v.clone()
          world.localToWorld(worldPos)
          worldPos.project(camera)
          const x = (worldPos.x * 0.5 + 0.5) * w
          const y = (-worldPos.y * 0.5 + 0.5) * h
          l.el.style.transform = `translate(${x}px, ${y}px) translate(-50%, ${l.below ? '70%' : '-150%'})`
          l.el.style.opacity = worldPos.z < 1 ? '1' : '0'
        })()
      }
      raf = requestAnimationFrame(tick)
    }
    tick()

    const ro = new ResizeObserver(() => {
      const w = el.clientWidth
      const h = el.clientHeight
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.position.z = fitDistance(w / h)
      camera.updateProjectionMatrix()
    })
    ro.observe(el)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      el.removeEventListener('mousemove', onMove)
      labels.forEach((l) => l.el.remove())
      disposables.forEach((d) => d.dispose())
      renderer.dispose()
      renderer.domElement.remove()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.mode, key])

  return <div ref={host} className="scene3d" style={{ height: props.height ?? 360 }} />
}
