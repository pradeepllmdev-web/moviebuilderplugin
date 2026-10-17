import { useEffect, useState } from 'react'
import { uploadMovieFile } from '../api/movieApi'
type Job = { id: string; name: string; status: string; stage?: string; completed: string[]; stages: string[]; error?: string; model?: { url: string }; demos: { mode: string; url: string; scene_url?: string; performance_url?: string }[] }
type Props = { apiBase: string; fileId?: number; name?: string; compact?: boolean }
const labels: Record<string, string> = { preflight: 'Checking services', model_and_body_rig: 'Generating model and body rig', face_landmarks: 'Finding the face', facial_controls: 'Fitting facial controls', animation_library: 'Adding body animations', validation: 'Checking controls', demo_videos: 'Rendering demo videos' }
export function CharacterWorkflow({ apiBase, fileId, name = 'New character', compact = false }: Props) {
  const [job, setJob] = useState<Job | null>(null)
  const [history, setHistory] = useState<Job[]>([])
  const [image, setImage] = useState<File | null>(null)
  const [characterName, setCharacterName] = useState(name)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [text, setText] = useState('Hello! I am ready for my character animation test.')
  const [sourceMouth, setSourceMouth] = useState('auto')
  const [gestureStrength, setGestureStrength] = useState(.18)
  async function request<T,>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const response = await fetch(`${apiBase}/api/character-workflows${path}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
    const data = await response.json()
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status})`)
    return data as T
  }
  useEffect(() => {
    let alive = true
    void request<Job[]>('').then(items => { if (alive) { setHistory(items); if (compact) setJob(items.find(j => j.name === name) ?? null) } }).catch(e => { if (alive) setError(String(e)) })
    return () => { alive = false }
  }, [apiBase, name, compact])
  const active = !!job && ['queued', 'running'].includes(job.status)
  useEffect(() => {
    if (!active || !job) return
    const timer = window.setInterval(() => { void request<Job>(`/${job.id}`).then(setJob).catch(e => setError(String(e))) }, 3000)
    return () => window.clearInterval(timer)
  }, [active, job?.id, apiBase])
  async function start() {
    setBusy(true); setError('')
    try {
      let id = fileId
      if (!id && image) { const uploaded = await uploadMovieFile(apiBase, image, 'image'); id = Number(uploaded.id) }
      if (!id) throw new Error('Choose a character image first')
      const made = await request<Job>('', 'POST', { reference_file_id: id, name: characterName, text, anatomy: 'biped', source_mouth: sourceMouth, gesture_strength: gestureStrength })
      setJob(made); setHistory(items => [made, ...items.filter(j => j.id !== made.id)])
    } catch (e) { setError(String(e)) } finally { setBusy(false) }
  }
  async function resume() {
    if (!job) return
    setBusy(true); setError('')
    try { setJob(await request<Job>(`/${job.id}/resume`, 'POST')) } catch (e) { setError(String(e)) } finally { setBusy(false) }
  }
  return <div className="character-workflow" style={{ marginTop: 12 }}>
    {!compact && <>
      <h3>Generate Character + Demo</h3>
      <p>Upload a clear full-body biped character image. Meshy generates the model and body rig. Facial fitting preserves its mouth anatomy, with calmer gestures, four full-body tests and a forest scene preview. Meshy credits are used. Results need visual review.</p>
      <label>Character name <input value={characterName} onChange={e => setCharacterName(e.target.value)} /></label>{' '}
      <label>Reference image <input type="file" accept="image/png,image/jpeg" onChange={e => setImage(e.target.files?.[0] ?? null)} /></label>
      <label style={{ display: 'block' }}>Demo dialogue <textarea value={text} onChange={e => setText(e.target.value)} maxLength={500} /></label>
      <label>Model mouth pose <select value={sourceMouth} onChange={e => setSourceMouth(e.target.value)}><option value="auto">Detect automatically</option><option value="open">Open — teeth and tongue visible</option><option value="closed">Closed or slight smile</option></select></label>{' '}
      <label>Talking gestures <select value={gestureStrength} onChange={e => setGestureStrength(Number(e.target.value))}><option value={0}>Quiet — head and face only</option><option value={.18}>Subtle</option><option value={.3}>Expressive</option></select></label>
      {history.length > 0 && <label>Existing jobs <select value={job?.id ?? ''} onChange={e => setJob(history.find(j => j.id === e.target.value) ?? null)}><option value="">Choose a job</option>{history.map(j => <option key={j.id} value={j.id}>{j.name} — {j.status}</option>)}</select></label>}
    </>}
    <button className="primary" disabled={busy || active || (!fileId && !image) || !characterName.trim() || !text.trim()} onClick={() => void start()}>{busy ? 'Starting…' : 'Generate Character + Demo'}</button>
    {compact && <small style={{ display: 'block' }}>Biped characters · uses Meshy credits</small>}
    {error && <p role="alert">{error}</p>}
    {job && <div aria-live="polite">
      <p>{job.status === 'needs_review' ? 'Demo ready — review the face, eyes and body before movie use.' : labels[job.stage ?? ''] ?? job.status} ({job.completed.length}/{job.stages.length} steps)</p>
      {job.error && <p role="alert">{job.error}</p>}
      {['needs_attention', 'interrupted'].includes(job.status) && <button disabled={busy} onClick={() => void resume()}>Resume saved job</button>}
      {job.model && <a href={`${apiBase}${job.model.url}`} target="_blank" rel="noreferrer">Download character model</a>}
      {job.demos.map(d => <div key={d.mode}><strong>{d.mode === 'scene' ? 'Forest scene preview' : d.mode}</strong><video controls preload="metadata" src={`${apiBase}${d.url}`} style={{ width: '100%', maxWidth: 768 }} />{d.scene_url && <a href={`${apiBase}${d.scene_url}`} download>Download editable Blender scene</a>}{d.performance_url && <>{' · '}<a href={`${apiBase}${d.performance_url}`} download>Download animated performance</a></>}</div>)}
    </div>}
  </div>
}
