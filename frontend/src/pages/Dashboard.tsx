import { useCallback, useEffect, useMemo, useState } from 'react';
import KPI from '../components/KPI';
import { apiGet, apiPost } from '../api/client';

type ChannelMetrics = {
  sent: number;
  replied: number;
  failed: number;
  reply_rate: number;
  failure_rate: number;
};

type KPIState = {
  reach: number;
  reply_rate: number;
  enrollment_rate: number;
  dropout_rate: number;
  event_counts: Record<string, number>;
  channel_effectiveness: Record<string, ChannelMetrics>;
};

type OptimizationState = {
  summary: Record<string, number>;
  recommendations: string[];
};

type CoverageState = {
  states_count: number;
  district_count: number;
  snapshot_count: number;
  latest_snapshot_ts: string | null;
};

type EventRow = {
  id: string;
  event_name: string;
  lead_id: string | null;
  campaign_id: string | null;
  channel: string | null;
  props: Record<string, unknown>;
  ts: string;
};

type PlanStep = { day_offset: number; channel: string; template_id: string };
type PlanChannel = { type: string; allocation_pct: number };
type PlanData = { channels?: PlanChannel[]; cadence?: { steps?: PlanStep[] } };
type DeployData = { status?: string; targeted_leads?: number; messages_queued?: number; messages_sent?: number; messages_failed?: number };
type ViewMode = 'overview' | 'operations' | 'raw';
type SortKey = 'sent' | 'replied' | 'reply_rate' | 'failure_rate';

type HistoryPoint = {
  ts: string;
  health: number;
  reply: number;
  enroll: number;
  dropout: number;
};

const seed = [
  ['MH', 'Maharashtra', 'D001', 'Pune', 130000, 42, 10.8, 185000, 74, 62],
  ['UP', 'Uttar Pradesh', 'D002', 'Lucknow', 165000, 36, 13.5, 126000, 58, 71],
  ['GJ', 'Gujarat', 'D003', 'Ahmedabad', 120000, 41, 9.1, 198000, 78, 54],
  ['RJ', 'Rajasthan', 'D004', 'Jaipur', 118000, 35.5, 11.4, 132000, 61, 68],
  ['MP', 'Madhya Pradesh', 'D005', 'Bhopal', 112000, 34, 12.7, 124000, 59, 72],
  ['BR', 'Bihar', 'D006', 'Patna', 172000, 29, 15.6, 98000, 49, 78],
  ['WB', 'West Bengal', 'D007', 'Kolkata', 121000, 38, 10.9, 142000, 67, 63],
  ['KA', 'Karnataka', 'D008', 'Bengaluru Urban', 140000, 45, 8.3, 214000, 82, 49],
  ['TN', 'Tamil Nadu', 'D009', 'Chennai', 132000, 44, 8.9, 209000, 80, 52],
  ['AP', 'Andhra Pradesh', 'D010', 'Visakhapatnam', 116000, 39, 10.1, 156000, 69, 61],
  ['TS', 'Telangana', 'D011', 'Hyderabad', 127000, 43, 8.7, 205000, 81, 51],
  ['OD', 'Odisha', 'D012', 'Bhubaneswar', 108000, 33, 12.2, 122000, 57, 74],
  ['KL', 'Kerala', 'D013', 'Thiruvananthapuram', 98000, 46, 7.1, 219000, 84, 46],
  ['HR', 'Haryana', 'D014', 'Gurugram', 101000, 40, 9.8, 231000, 79, 53],
  ['PB', 'Punjab', 'D015', 'Ludhiana', 97000, 39, 9.5, 188000, 72, 58],
] as const;

const regionalRows = seed.map(([state_code, state_name, district_code, district_name, youth_population, female_participation_rate, unemployment_rate, median_household_income, internet_penetration_rate, skill_gap_index]) => ({
  state_code,
  state_name,
  district_code,
  district_name,
  youth_population,
  female_participation_rate,
  unemployment_rate,
  median_household_income,
  internet_penetration_rate,
  skill_gap_index,
  top_skills: ['service', 'retail'],
  demand_skills: ['digital_support', 'operations'],
}));

function pct(v: number | undefined): string {
  return `${(((v ?? 0) * 100) || 0).toFixed(1)}%`;
}

function dateTime(v: string | null | undefined): string {
  if (!v) return 'No snapshots yet';
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v : d.toLocaleString();
}

function score(k: KPIState | null): number {
  if (!k) return 0;
  const reach = Math.min(k.reach / 100, 1);
  const reply = Math.min(k.reply_rate * 2.5, 1);
  const enroll = Math.min(k.enrollment_rate * 2, 1);
  const dropout = 1 - Math.min(k.dropout_rate * 2, 1);
  return Math.round((reach * 0.22 + reply * 0.28 + enroll * 0.35 + dropout * 0.15) * 100);
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  const width = 240;
  const height = 64;
  if (values.length < 2) return <div className="spark-empty">Need 2+ refreshes</div>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);
  const points = values.map((v, i) => `${i * step},${height - ((v - min) / range) * height}`).join(' ');
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="sparkline">
      <polyline points={points} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIState | null>(null);
  const [coverage, setCoverage] = useState<CoverageState | null>(null);
  const [optimization, setOptimization] = useState<OptimizationState | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [lastPlan, setLastPlan] = useState<PlanData | null>(null);
  const [lastDeploy, setLastDeploy] = useState<DeployData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [view, setView] = useState<ViewMode>('overview');
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshSec, setRefreshSec] = useState(30);
  const [refreshAt, setRefreshAt] = useState('');
  const [eventQuery, setEventQuery] = useState('');
  const [eventType, setEventType] = useState('all');
  const [sortKey, setSortKey] = useState<SortKey>('sent');
  const [sortDesc, setSortDesc] = useState(true);
  const [simLeads, setSimLeads] = useState(800);
  const [simLift, setSimLift] = useState(5);

  const refresh = useCallback(async () => {
    try {
      const [k, c, o, ev] = (await Promise.all([
        apiGet('/analytics/kpis'),
        apiGet('/data/coverage'),
        apiGet('/analytics/optimize'),
        apiGet('/analytics/events?limit=100'),
      ])) as [KPIState, CoverageState, OptimizationState, EventRow[]];
      setKpis(k);
      setCoverage(c);
      setOptimization(o);
      setEvents(ev);
      const health = score(k);
      setHistory((prev) => [...prev, { ts: new Date().toISOString(), health, reply: k.reply_rate * 100, enroll: k.enrollment_rate * 100, dropout: k.dropout_rate * 100 }].slice(-36));
      setRefreshAt(new Date().toLocaleTimeString());
      setError('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Refresh failed');
    }
  }, []);

  const exportSnapshot = useCallback(() => {
    const data = { at: new Date().toISOString(), kpis, coverage, optimization, lastPlan, lastDeploy, events: events.slice(0, 40), history };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `outreach-dashboard-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [coverage, events, history, kpis, lastDeploy, lastPlan, optimization]);

  async function runDemo() {
    setRunning(true);
    try {
      await apiPost('/data/ingest/regional-skill', { rows: regionalRows });
      const leads = [
        { id: 'L3001', first_name: 'Asha', age_band: '18-21', district_code: 'D001', preferred_language: 'hi', digital_literacy_level: 'medium', employment_status: 'unemployed', household_income_band: 'low', consent_sms: true, consent_whatsapp: true },
        { id: 'L3002', first_name: 'Ravi', age_band: '22-25', district_code: 'D006', preferred_language: 'en', digital_literacy_level: 'low', employment_status: 'underemployed', household_income_band: 'lower_middle', consent_sms: true, consent_voice: true },
        { id: 'L3003', first_name: 'Meera', age_band: '26-29', district_code: 'D012', preferred_language: 'en', digital_literacy_level: 'medium', employment_status: 'student', household_income_band: 'middle', consent_email: true, consent_whatsapp: true },
      ];
      for (const lead of leads) {
        await apiPost('/leads', lead);
        await apiPost(`/leads/${lead.id}/score`, {});
      }
      await apiPost('/campaigns', { id: 'C3001', name: 'Statewide Youth Enrollment Drive', goal: 'onboarding_start', segment_filter: { district_code: ['D001', 'D006', 'D012'], min_propensity: 0.5 } });
      await apiPost('/campaigns/C3001/approve', { approved_by: 'admin_automation' });
      setLastPlan((await apiPost('/campaigns/C3001/plan', {})) as PlanData);
      setLastDeploy((await apiPost('/campaigns/C3001/deploy', { batch_limit: 50, dry_run: false, cta_link: 'https://example.org/apply' })) as DeployData);
      await apiPost('/messages/reply', { campaign_id: 'C3001', lead_id: 'L3001', channel: 'whatsapp', sentiment: 'positive', intent: 'interested' });
      const started = (await apiPost('/onboarding/start', { lead_id: 'L3001', program_id: 'P101' })) as { case_id: string };
      await apiPost(`/onboarding/${started.case_id}/documents`, { document_type: 'id_proof', document_ref: 'https://files.example/id-l3001.pdf' });
      await apiPost(`/onboarding/${started.case_id}/reminder`, { note: 'Please complete orientation this week.' });
      await apiPost(`/onboarding/${started.case_id}/step`, { state: 'orientation_pending', current_step: 'orientation' });
      await apiPost(`/onboarding/${started.case_id}/step`, { state: 'confirmed', current_step: 'confirmation' });
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Pipeline failed');
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(refresh, Math.max(10, refreshSec) * 1000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, refresh, refreshSec]);

  const health = useMemo(() => score(kpis), [kpis]);
  const lastPoint = history.length > 1 ? history[history.length - 2] : undefined;
  const replyDelta = useMemo(() => {
    if (!kpis || !lastPoint) return 'n/a';
    return `${kpis.reply_rate * 100 - lastPoint.reply >= 0 ? '+' : ''}${(kpis.reply_rate * 100 - lastPoint.reply).toFixed(1)}pp`;
  }, [kpis, lastPoint]);

  const channelRows = useMemo(() => Object.entries(kpis?.channel_effectiveness ?? {}).sort((a, b) => (sortDesc ? b[1][sortKey] - a[1][sortKey] : a[1][sortKey] - b[1][sortKey])), [kpis, sortDesc, sortKey]);
  const topEvents = useMemo(() => Object.entries(kpis?.event_counts ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 10), [kpis]);
  const eventTypes = useMemo(() => ['all', ...Array.from(new Set(events.map((e) => e.event_name)))], [events]);
  const filteredEvents = useMemo(() => events.filter((e) => (eventType === 'all' || e.event_name === eventType) && `${e.event_name} ${e.channel ?? ''} ${e.lead_id ?? ''} ${e.campaign_id ?? ''}`.toLowerCase().includes(eventQuery.toLowerCase())).slice(0, 20), [eventQuery, eventType, events]);
  const steps = useMemo(() => lastPlan?.cadence?.steps ?? [], [lastPlan]);
  const channels = useMemo(() => lastPlan?.channels ?? [], [lastPlan]);
  const forecast = useMemo(() => {
    const replyRate = Math.min((kpis?.reply_rate ?? 0) + simLift / 100, 1);
    const replies = Math.round(simLeads * replyRate);
    const enroll = Math.round(replies * Math.max(kpis?.enrollment_rate ?? 0.1, 0.1));
    return { replyRate, replies, enroll };
  }, [kpis?.enrollment_rate, kpis?.reply_rate, simLeads, simLift]);

  return (
    <div className="dashboard-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="container">
        <section className="hero reveal">
          <div>
            <p className="eyebrow">Outreach Control Room</p>
            <h1>Automated Outreach and Enrollment Dashboard</h1>
            <p className="hero-copy">Advanced command view for data integration, targeting, campaign execution, onboarding automation, and optimization.</p>
            <div className="status-row">
              <span className={`pill ${kpis ? 'ok' : 'warn'}`}>{kpis ? 'Backend Connected' : 'Waiting For Data'}</span>
              <span className="pill neutral">Last refresh: {refreshAt || 'Not yet'}</span>
              <span className="pill neutral">Telemetry points: {history.length}</span>
            </div>
          </div>
          <div className="hero-actions">
            <div className="btn-cluster">
              <button className="btn btn-ghost" onClick={refresh}>Refresh Metrics</button>
              <button className="btn btn-primary" onClick={runDemo} disabled={running}>{running ? 'Running Pipeline...' : 'Run Full Pipeline Demo'}</button>
              <button className="btn btn-ghost" onClick={exportSnapshot}>Export Snapshot</button>
            </div>
            <div className="inline-controls">
              <label className="switch"><input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} /><span>Auto refresh</span></label>
              <label className="refresh-picker">Every<select value={refreshSec} onChange={(e) => setRefreshSec(Number(e.target.value))}><option value={15}>15s</option><option value={30}>30s</option><option value={60}>60s</option></select></label>
            </div>
          </div>
        </section>

        <section className="toolbar reveal">
          <button className={`tab ${view === 'overview' ? 'active' : ''}`} onClick={() => setView('overview')}>Overview</button>
          <button className={`tab ${view === 'operations' ? 'active' : ''}`} onClick={() => setView('operations')}>Operations</button>
          <button className={`tab ${view === 'raw' ? 'active' : ''}`} onClick={() => setView('raw')}>Raw Data</button>
        </section>

        {error && <div className="card error reveal">{error}</div>}

        {view === 'overview' && (
          <>
            <section className="kpi-grid reveal">
              <KPI label="Reach" value={kpis?.reach ?? 0} note="Outbound successful sends" tone="accent" />
              <KPI label="Reply Rate" value={pct(kpis?.reply_rate)} note={`Delta ${replyDelta}`} tone={(kpis?.reply_rate ?? 0) >= 0.2 ? 'good' : 'warn'} />
              <KPI label="Enrollment Rate" value={pct(kpis?.enrollment_rate)} note="Funnel conversion" tone={(kpis?.enrollment_rate ?? 0) >= 0.2 ? 'good' : 'warn'} />
              <KPI label="Dropout Rate" value={pct(kpis?.dropout_rate)} note="Lower is better" tone={(kpis?.dropout_rate ?? 0) <= 0.15 ? 'good' : 'warn'} />
            </section>

            <section className="insight-grid reveal">
              <article className="card panel score-panel">
                <h3>Performance Health</h3>
                <div className="score-ring-wrap">
                  <div className="score-ring" style={{ ['--score' as string]: `${health}` }}><span>{health}</span></div>
                  <div className="score-meta">
                    <p>Composite performance score built from reach, reply, enrollment, and dropout quality.</p>
                    <div className="alert-stack">
                      {(coverage?.states_count ?? 0) < 15 && <span className="alert-pill critical">Coverage below 15 states.</span>}
                      {(kpis?.reply_rate ?? 0) < 0.08 && <span className="alert-pill warn">Reply rate is low.</span>}
                      {(kpis?.dropout_rate ?? 0) > 0.2 && <span className="alert-pill warn">Dropout rate elevated.</span>}
                      {(coverage?.states_count ?? 0) >= 15 && (kpis?.reply_rate ?? 0) >= 0.08 && (kpis?.dropout_rate ?? 0) <= 0.2 && <span className="alert-pill info">System operating in stable range.</span>}
                    </div>
                  </div>
                </div>
              </article>

              <article className="card panel">
                <h3>Coverage Snapshot</h3>
                <div className="metric-row"><span>States</span><strong>{coverage?.states_count ?? 0}</strong></div>
                <div className="metric-row"><span>Districts</span><strong>{coverage?.district_count ?? 0}</strong></div>
                <div className="metric-row"><span>Skill Snapshots</span><strong>{coverage?.snapshot_count ?? 0}</strong></div>
                <p className="caption">Latest sync: {dateTime(coverage?.latest_snapshot_ts)}</p>
              </article>

              <article className="card panel">
                <h3>Optimization Recommendations</h3>
                <ul className="list">{(optimization?.recommendations ?? ['No recommendations yet']).map((r, i) => <li key={`${r}-${i}`}>{r}</li>)}</ul>
              </article>
            </section>

            <section className="trend-grid reveal">
              <article className="card panel"><h3>Health Trend</h3><Sparkline values={history.map((h) => h.health)} color="#0f7c90" /></article>
              <article className="card panel"><h3>Reply Trend</h3><Sparkline values={history.map((h) => h.reply)} color="#1f8f5c" /></article>
              <article className="card panel"><h3>Enrollment Trend</h3><Sparkline values={history.map((h) => h.enroll)} color="#eb7c2b" /></article>
              <article className="card panel"><h3>Dropout Trend</h3><Sparkline values={history.map((h) => h.dropout)} color="#bd7b12" /></article>
            </section>
          </>
        )}

        {view === 'operations' && (
          <section className="ops-grid reveal">
            <article className="card panel wide">
              <div className="panel-head">
                <h3>Channel Effectiveness</h3>
                <div className="sort-controls">
                  <label>Sort by<select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}><option value="sent">Sent</option><option value="replied">Replied</option><option value="reply_rate">Reply rate</option><option value="failure_rate">Failure rate</option></select></label>
                  <button className="btn btn-ghost tiny" onClick={() => setSortDesc((p) => !p)}>{sortDesc ? 'Desc' : 'Asc'}</button>
                </div>
              </div>
              <table className="matrix">
                <thead><tr><th>Channel</th><th>Sent</th><th>Replies</th><th>Reply Rate</th><th>Failure Rate</th></tr></thead>
                <tbody>
                  {channelRows.length === 0 && <tr><td colSpan={5}>No channel data yet.</td></tr>}
                  {channelRows.map(([channel, m]) => <tr key={channel}><td>{channel}</td><td>{m.sent}</td><td>{m.replied}</td><td>{pct(m.reply_rate)}</td><td>{pct(m.failure_rate)}</td></tr>)}
                </tbody>
              </table>
            </article>

            <article className="card panel"><h3>Current Plan Allocation</h3><div className="bars">{channels.length === 0 && <p className="caption">Run demo to generate plan.</p>}{channels.map((c) => <div key={c.type} className="bar-row"><div className="bar-label">{c.type}</div><div className="bar-track"><span style={{ width: `${c.allocation_pct}%` }} /></div><div className="bar-value">{c.allocation_pct}%</div></div>)}</div></article>
            <article className="card panel"><h3>Cadence Timeline</h3><ol className="timeline">{steps.length === 0 && <li>No cadence steps yet.</li>}{steps.map((s, i) => <li key={`${s.channel}-${i}`}><span className="time">Day {s.day_offset}</span><span className="event">{s.channel}</span><span className="template">{s.template_id}</span></li>)}</ol></article>

            <article className="card panel">
              <h3>Scenario Simulator</h3>
              <label className="slider-row">Simulated Leads<input type="range" min={100} max={5000} step={100} value={simLeads} onChange={(e) => setSimLeads(Number(e.target.value))} /><strong>{simLeads}</strong></label>
              <label className="slider-row">Reply Lift<input type="range" min={0} max={20} step={1} value={simLift} onChange={(e) => setSimLift(Number(e.target.value))} /><strong>+{simLift}pp</strong></label>
              <div className="metric-row"><span>Projected Reply Rate</span><strong>{pct(forecast.replyRate)}</strong></div>
              <div className="metric-row"><span>Expected Replies</span><strong>{forecast.replies}</strong></div>
              <div className="metric-row"><span>Expected Enrollments</span><strong>{forecast.enroll}</strong></div>
            </article>

            <article className="card panel wide">
              <div className="panel-head">
                <h3>Live Event Stream</h3>
                <div className="event-filters">
                  <input type="text" placeholder="Search events" value={eventQuery} onChange={(e) => setEventQuery(e.target.value)} />
                  <select value={eventType} onChange={(e) => setEventType(e.target.value)}>{eventTypes.map((t) => <option key={t} value={t}>{t}</option>)}</select>
                </div>
              </div>
              <div className="event-stream">
                {filteredEvents.length === 0 && <p className="caption">No matching events.</p>}
                {filteredEvents.map((e) => <div key={e.id} className="event-card"><div className="event-main"><strong>{e.event_name}</strong><span>{new Date(e.ts).toLocaleString()}</span></div><div className="event-meta"><span>lead: {e.lead_id ?? '-'}</span><span>campaign: {e.campaign_id ?? '-'}</span><span>channel: {e.channel ?? '-'}</span></div></div>)}
              </div>
            </article>
          </section>
        )}

        {view === 'raw' && (
          <section className="raw-grid reveal">
            <article className="card panel"><h3>KPI Payload</h3><pre>{JSON.stringify(kpis ?? {}, null, 2)}</pre></article>
            <article className="card panel"><h3>Coverage Payload</h3><pre>{JSON.stringify(coverage ?? {}, null, 2)}</pre></article>
            <article className="card panel"><h3>Optimization Payload</h3><pre>{JSON.stringify(optimization ?? {}, null, 2)}</pre></article>
            <article className="card panel"><h3>Last Campaign Plan</h3><pre>{JSON.stringify(lastPlan ?? {}, null, 2)}</pre></article>
            <article className="card panel"><h3>Last Deploy Result</h3><pre>{JSON.stringify(lastDeploy ?? {}, null, 2)}</pre></article>
            <article className="card panel"><h3>Top Event Counts</h3><pre>{JSON.stringify(Object.fromEntries(topEvents), null, 2)}</pre></article>
          </section>
        )}
      </div>
    </div>
  );
}
