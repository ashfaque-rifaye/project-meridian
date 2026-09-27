import { createContext, ReactNode, useCallback, useContext, useRef, useState } from 'react'
import { post, useDataVersion } from './api'

export type AgentState = { id: string; name: string; stage: string; skill: string; bob: string; status: string; summary?: string; duration_ms?: number }

type Inv = {
  id: string | null
  status: 'idle' | 'running' | 'done' | 'error'
  agents: Record<string, AgentState>
  order: string[]
  logs: { agent: string; text: string; t_ms: number }[]
  stage: string | null
  stagesDone: string[]
  result: any
  error: string | null
  startedAt: number | null
  pace: number
  start: (pace?: number) => Promise<void>
}

const Ctx = createContext<Inv | null>(null)

export function useInvestigation() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('InvestigationProvider missing')
  return ctx
}

export function InvestigationProvider({ children }: { children: ReactNode }) {
  const { bump } = useDataVersion()
  const [state, setState] = useState<Omit<Inv, 'start'>>({
    id: null, status: 'idle', agents: {}, order: [], logs: [], stage: null, stagesDone: [], result: null, error: null,
    startedAt: null, pace: 450,
  })
  const source = useRef<EventSource | null>(null)

  const start = useCallback(async (pace = 450) => {
    source.current?.close()
    setState((s) => ({ ...s, status: 'running', agents: {}, order: [], logs: [], stage: null, stagesDone: [], result: null, error: null, startedAt: Date.now(), pace }))
    const { investigation_id } = await post('/investigations', { environment: 'prod', reference: 'stage', pace_ms: pace })
    setState((s) => ({ ...s, id: investigation_id }))
    const es = new EventSource(`/api/investigations/${investigation_id}/events`)
    source.current = es
    es.onmessage = (msg) => {
      const e = JSON.parse(msg.data)
      setState((s) => {
        switch (e.type) {
          case 'start': {
            const agents: Record<string, AgentState> = {}
            for (const a of e.agents) agents[a.id] = { ...a, status: 'queued' }
            return { ...s, agents, order: e.agents.map((a: any) => a.id) }
          }
          case 'stage':
            return { ...s, stage: e.stage, stagesDone: s.stage ? [...s.stagesDone, s.stage] : s.stagesDone }
          case 'agent': {
            const prev = s.agents[e.agent] || ({ id: e.agent } as AgentState)
            return {
              ...s,
              agents: { ...s.agents, [e.agent]: { ...prev, status: e.status, summary: e.summary || prev.summary, duration_ms: e.detail?.duration_ms ?? prev.duration_ms } },
            }
          }
          case 'log':
            return { ...s, logs: [...s.logs, { agent: e.agent, text: e.text, t_ms: e.t_ms }] }
          case 'complete':
            return { ...s, status: 'done', result: e.result, stagesDone: [...s.stagesDone, s.stage || 'PROVE'], stage: null }
          case 'error':
            return { ...s, status: 'error', error: e.message }
          default:
            return s
        }
      })
      if (e.type === 'complete' || e.type === 'error') bump()
    }
    es.addEventListener('end', () => es.close())
    es.onerror = () => es.close()
  }, [bump])

  return <Ctx.Provider value={{ ...state, start }}>{children}</Ctx.Provider>
}
