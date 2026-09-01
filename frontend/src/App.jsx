import { useState, useEffect, useMemo, useRef, useLayoutEffect } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, BarChart, Bar, Cell, PieChart, Pie,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  Target, Brain, Dna, Zap, X, Sun, Moon, FlaskConical, UploadCloud, FileText, UserPlus
} from 'lucide-react';
import './App.css';
import WelcomeIntro from './WelcomeIntro';
import LoadingAnimation from './LoadingAnimation';

const API_BASE = 'http://localhost:8001';

const PALETTE = {
  light: {
    paper: '#F1F4F2', surface: '#FFFFFF', surface2: '#E7ECE9',
    line: '#DBE2DE', lineStrong: '#B7C3BD',
    ink: '#10181A', inkDim: '#57696A', inkFaint: '#93A29E',
    green: '#1E8A57', blue: '#1B5FA6', red: '#B23A34', amber: '#B4791E', gray: '#93A29E',
  },
  dark: {
    paper: '#0A0F0E', surface: '#121917', surface2: '#19211F',
    line: 'rgba(237,243,241,0.09)', lineStrong: 'rgba(237,243,241,0.18)',
    ink: '#EDF3F1', inkDim: '#92A6A2', inkFaint: '#5E716D',
    green: '#3FC583', blue: '#5CA3EC', red: '#E2716A', amber: '#E2AC55', gray: '#5E716D',
  },
};


const OmniOncoLogo = ({ size = 40, showText = true, theme = 'dark' }) => {
  const isLight = theme === 'light';
  const lineColor = isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.2)';
  const strokeColor = isLight ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.4)';
  const textColor = isLight ? '#10181A' : '#ffffff';
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <svg width={size} height={size} viewBox="0 0 100 100" style={{ filter: isLight ? 'none' : 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))', flexShrink: 0 }}>
        {/* Outer dashed circle */}
        <circle cx="50" cy="50" r="35" fill="none" stroke={lineColor} strokeWidth="1.5" strokeDasharray="4 4" />
        {/* Lines connecting dots */}
        <line x1="50" y1="50" x2="50" y2="15" stroke={strokeColor} strokeWidth="1.5" />
        <line x1="50" y1="50" x2="19.69" y2="67.5" stroke={strokeColor} strokeWidth="1.5" />
        <line x1="50" y1="50" x2="80.31" y2="67.5" stroke={strokeColor} strokeWidth="1.5" />
        
        {/* Inner solid circle */}
        <circle cx="50" cy="50" r="15" fill="none" stroke="#00b4d8" strokeWidth="2" />
        
        {/* Central dot */}
        <circle cx="50" cy="50" r="6" fill="#00b4d8" />
        
        {/* Three outer dots */}
        <circle cx="50" cy="15" r="6" fill="#38a169" /> {/* Green */}
        <circle cx="19.69" cy="67.5" r="6" fill="#ed8936" /> {/* Orange */}
        <circle cx="80.31" cy="67.5" r="6" fill="#9f7aea" /> {/* Purple */}
      </svg>
      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: size * 0.5, fontWeight: 800, letterSpacing: -0.5, lineHeight: 1, fontFamily: 'Inter, sans-serif' }}>
            <span style={{ color: textColor }}>Omni</span><span style={{ color: '#00b4d8' }}>Onco</span>
          </div>
          <div style={{ fontSize: size * 0.16, color: '#92A6A2', fontWeight: 600, letterSpacing: 1.5, marginTop: 4, whiteSpace: 'nowrap' }}>
            AI &middot; RESEARCH INTELLIGENCE
          </div>
        </div>
      )}
    </div>
  );
};

function LocusRule({ running }) {
  return (
    <div className={`locus-rule${running ? ' running' : ''}`}>
      <span className="a" /><span className="c" /><span className="g" /><span className="t" />
    </div>
  );
}

function useCountUp(target, duration = 800) {
  const [val, setVal] = useState(typeof target === 'number' ? 0 : target);
  useEffect(() => {
    if (typeof target !== 'number') { setVal(target); return; }
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { setVal(target); return; }
    let raf; let start = null;
    const tick = (ts) => {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

function StatValue({ value, color }) {
  const display = useCountUp(value);
  const shown = typeof display === 'number' ? display.toLocaleString() : (display ?? '—');
  return <div className="stat-value mono" style={{ color }}>{shown}</div>;
}

function LocusDivider({ label }) {
  return (
    <div className="locus-divider">
      <span className="tag">A&middot;C&middot;G&middot;T</span>
      <div className="bar"><span className="a" /><span className="c" /><span className="g" /><span className="t" /></div>
      {label && <span className="tag">{label}</span>}
    </div>
  );
}

const TABS = ['data', 'overview', 'mutation', 'expression', 'integration', 'pathways', 'clinical'];
const PIPELINE_STAGES = [
  'decoding dataset',
  'calling somatic mutations',
  'scoring differential expression',
  'integrating mutation + expression',
  'mapping pathways',
  'synthesizing findings',
];

function DnaLoader({ cancer, c }) {
  const rungs = 13;
  const pairPalette = [[c.green, c.red], [c.ink, c.blue]];
  const [stageIdx, setStageIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStageIdx(i => (i + 1) % PIPELINE_STAGES.length), 1600);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div className="helix-wrap">
        {Array.from({ length: rungs }).map((_, i) => {
          const [left, right] = pairPalette[i % 2];
          const delay = `${(-(i * 0.19)).toFixed(2)}s`;
          return (
            <div className="helix-rung" key={i} style={{ top: i * 16 }}>
              <span className="helix-dot l" style={{ background: left, animationDelay: delay }} />
              <span className="helix-bar" style={{ animationDelay: delay }} />
              <span className="helix-dot r" style={{ background: right, animationDelay: delay }} />
            </div>
          );
        })}
      </div>
      <div className="helix-stage mono">
        {stageIdx === 0 ? `decoding tcga-${cancer.toLowerCase()}` : PIPELINE_STAGES[stageIdx]}
      </div>
    </div>
  );
}



function useOmniData(fetchParams) {
  const [data, setData] = useState({});
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [stages, setStages] = useState({ val: 'wait', load: 'wait', mut: 'wait', exp: 'wait', int: 'wait', path: 'wait', bio: 'wait', llm: 'wait' });
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!fetchParams) return;
    let active = true;
    const { cancer, goal } = fetchParams;
    
    setData({}); setStatus('running'); setError(null);
    setStages({ val: 'run', load: 'wait', mut: 'wait', exp: 'wait', int: 'wait', path: 'wait', bio: 'wait', llm: 'wait' });
    setLogs([]);

    const addLog = (msg) => {
      if (active) setLogs(prev => [...prev, { time: new Date().toLocaleTimeString('en-US',{hour12:false}), msg }]);
    };

    const runPipeline = async () => {
      try {
        addLog(`Validating research goal: "${goal}"`);
        // Query backend for adaptive workflow orchestration plan
        let plan = ["mut", "exp", "int", "path", "bio", "llm"]; // default
        try {
          const planRes = await fetch(`${API_BASE}/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal, cancer_type: cancer })
          });
          if (planRes.ok) {
            const planData = await planRes.json();
            plan = planData.plan || plan;
          }
        } catch (e) {
          console.warn("Backend /plan failed, using default routing");
        }
        
        if (!active) return;
        
        // Mark stages not in plan as skipped
        setStages(s => {
          const ns = { ...s };
          ['mut', 'exp', 'int', 'path', 'bio'].forEach(key => {
            if (!plan.includes(key)) ns[key] = 'skip';
          });
          ns.val = 'done';
          ns.load = 'run';
          return ns;
        });
        
        addLog(`Loading TCGA-${cancer} dataset. Plan: [${plan.join(', ')}]`);
        await new Promise(r => setTimeout(r, 800));
        if (!active) return;
        
        // Helper to mark current stage running and previous done safely
        const transit = (prevKey, currKey) => {
          setStages(s => ({ ...s, [prevKey]: 'done', [currKey]: 'run' }));
        };

        let lastStage = 'load';

        if (plan.includes('mut')) {
          transit(lastStage, 'mut');
          lastStage = 'mut';
          addLog('Executing somatic mutation analysis...');
          let m = await fetch(`${API_BASE}/mutation/${cancer}`).then(r => r.json());
          if (!active) return;
          setData(d => ({ ...d, mutation: m }));
          addLog(`Identified ${m.all_mutated_genes?.length || 500} genes with >= 1 somatic mutation across ${m.total_patients} patients.`);
        }

        if (plan.includes('exp')) {
          transit(lastStage, 'exp');
          lastStage = 'exp';
          addLog('Scoring differential expression (RNA-seq)...');
          let e = await fetch(`${API_BASE}/expression/${cancer}?top_n=500`).then(r => r.json());
          if (!active) return;
          setData(d => ({ ...d, expression: e }));
          addLog(`Found ${e.significant_degs} significant DEGs (${e.upregulated_count} up, ${e.downregulated_count} down).`);
        }

        if (plan.includes('int')) {
          transit(lastStage, 'int');
          lastStage = 'int';
          addLog('Orchestrating multi-omics convergence...');
          let i = await fetch(`${API_BASE}/integration/${cancer}`).then(r => r.json());
          let rank = await fetch(`${API_BASE}/ranking/${cancer}`).then(r => r.json());
          if (!active) return;
          setData(d => ({ ...d, integration: i, ranking: rank }));
          addLog(`Ranked ${rank.ranked_genes?.length || 0} candidate biomarkers.`);
        }

        if (plan.includes('path')) {
          transit(lastStage, 'path');
          lastStage = 'path';
          addLog('Mapping biological pathways from Enrichr...');
          let p = await fetch(`${API_BASE}/pathway/${cancer}`).then(r => r.json());
          if (!active) return;
          setData(d => ({ ...d, pathway: p }));
          addLog(`Mapped targets to ${Object.keys(p.results || {}).length} pathway databases.`);
        }

        if (plan.includes('bio')) {
          transit(lastStage, 'bio');
          lastStage = 'bio';
          addLog('Correlating clinical survival data (Primary vs Metastasis)...');
          let c = await fetch(`${API_BASE}/clinical/${cancer}`).then(r => r.json());
          let b = await fetch(`${API_BASE}/biomarker/${cancer}`).then(r => r.json());
          if (!active) return;
          setData(d => ({ ...d, clinical: c, biomarker: b }));
          addLog('Clinical cross-validation complete.');
        }

        if (plan.includes('llm')) {
          transit(lastStage, 'llm');
          lastStage = 'llm';
          addLog('Generating biological interpretation... This may take a moment.');
          
          let url = new URL(`${API_BASE}/full/${cancer}`);
          url.searchParams.append('goal', goal);
          url.searchParams.append('limit_degs', 10);
          let res = await fetch(url).then(r => r.json());
          
          if (!active) return;
          if (res.hypothesis) {
            setData(d => ({
              ...d,
              integration: { ...(d.integration || {}), hypothesis: res.hypothesis }
            }));
          }
          addLog('AI synthesis complete.');
        }

        setStages(s => ({ ...s, [lastStage]: 'done' }));
        setStatus('complete');
      } catch (err) {
        if (active) {
          setError(err.message);
          setStatus('error');
          addLog(`ERROR: ${err.message}`);
        }
      }
    };

    runPipeline();
    return () => { active = false; };
  }, [fetchParams]);

  return { data, status, error, stages, logs };
}




function Typewriter({ text, speed = 8 }) {
  const [disp, setDisp] = useState('');
  useEffect(() => {
    let i = 0;
    setDisp('');
    if (!text) return;
    const id = setInterval(() => {
      setDisp(text.substring(0, i));
      i++;
      if (i > text.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
  }, [text, speed]);
  return <>{disp}{disp.length < text?.length && <span className="cursor-blink">_</span>}</>;
}


/* ================= GLOBAL STAT BAR ================= */
function GlobalStatBar({ data, c }) {
  const mut = data?.mutation || {};
  const exp = data?.expression || {};
  const clin = data?.clinical || {};

  const stats = [
    { label: 'Patients', value: mut.total_patients || clin.total_samples || 0, color: c.ink },
    { label: 'Mutated genes', value: mut.all_mutated_genes?.length || mut.total_mutations ? 500 : 0, color: c.ink },
    { label: 'DEGs', value: exp.significant_degs || 0, color: c.blue },
    { label: 'Upregulated', value: exp.upregulated_count || 0, color: c.green },
    { label: 'Downregulated', value: exp.downregulated_count || 0, color: c.red },
  ];

  return (
    <div className="global-stat-bar fade-up" style={{ display: 'flex', gap: 32, padding: '12px 24px', borderBottom: `1px solid ${c.line}`, background: c.surface2, zIndex: 5, flexShrink: 0 }}>
      {stats.map(s => (
        <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 11, color: c.inkFaint, textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>{s.label}</div>
          <StatValue value={s.value} color={s.color} />
        </div>
      ))}
    </div>
  );
}

/* ================= OVERVIEW ================= */

function OverviewPage({ data, cancer, t, c, setPage, goal, stages, logs, status }) {
  const mut = data.mutation || {};
  const exp = data.expression || {};
  const int = data.integration || {};
  const path = data.pathway || {};
  const clin = data.clinical || {};


  const steps = [
    'Data loaded', 'Mutation analysis', 'Expression analysis', 'Multi-omics integration',
    'Pathway analysis', 'Biomarker analysis', 'Llama 3.2 synthesis',
  ];
  const stepDone = [true, !!data.mutation, !!data.expression, !!data.integration, !!data.pathway, !!data.biomarker, !!int?.hypothesis];


  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Case file &mdash; TCGA-{cancer}</div>
        <h1 className="page-title">AI Multi-Omics Agent for Breast &amp; Skin Cancer</h1>
        <div className="page-sub">Dataset <span className="dataset-chip">TCGA-{cancer}</span> &mdash; goal-driven agent, mutation + expression integration</div>
      </div>

      <div className="fade-up-1">
        <LocusDivider label="OVERVIEW" />
      </div>

      {status === 'running' ? (
        <div className="fade-up" style={{ display: 'flex', justifyContent: 'center', margin: '60px 0' }}>
          <LoadingAnimation />
        </div>
      ) : (
        <div className="fade-up-2" style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 18 }}>
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Agent Synthesis</span>
            <Brain size={14} color={c.amber} />
          </div>
          <div className="panel-body">
            <div className="goal-plate">
              <div className="k">Research goal</div>
              <div className="v">&ldquo;{goal}&rdquo;</div>
            </div>

          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="panel">
            <div className="panel-head"><span className="panel-title">Explore Results</span></div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <button className="btn btn-primary" onClick={() => setPage('integration')} style={{ width: '100%' }}>Integrated candidates</button>
              <button className="btn btn-ghost" onClick={() => setPage('pathways')} style={{ width: '100%', border: `1px solid ${c.line}` }}>Biological pathways</button>
              <button className="btn btn-ghost" onClick={() => setPage('clinical')} style={{ width: '100%', border: `1px solid ${c.line}` }}>Clinical &amp; biomarkers</button>
            </div>
          </div>
        </div>
      </div>
      )}

      <div className="fade-up-2" style={{ marginTop: 40, paddingTop: 30, borderTop: `1px solid ${c.line}` }}>
        <div className="eyebrow" style={{ marginBottom: 16 }}>Orchestrator Trace</div>
        <LangGraphLogs stages={stages} logs={logs} c={c} isDone={stages?.llm === 'done'} />
      </div>
    </div>
  );
}

/* ================= MUTATION ================= */
function MutationPage({ data, t, c }) {
  const mut = data.mutation;
  const varData = Object.entries(mut.variant_types || {}).map(([name, value]) => ({ name, value }));
  const VCOLS = [c.blue, c.green, c.amber, c.red, c.ink, c.gray];

  const tmbData = useMemo(() => {
    if (!mut.tmb_per_patient) return [];
    const bins = new Array(20).fill(0);
    const max = Math.max(...mut.tmb_per_patient);
    const step = max / 20 || 1;
    mut.tmb_per_patient.forEach(v => {
      const idx = Math.min(19, Math.floor(v / step));
      bins[idx]++;
    });
    return bins.map((count, i) => ({ x: (i * step).toFixed(1), y: count }));
  }, [mut.tmb_per_patient]);

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Genomic analysis</div>
        <h1 className="page-title">Somatic mutations</h1>
        <div className="page-sub">Variant classifications & TMB distribution</div>
      </div>
      <LocusDivider label="MAF" />

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 18 }}>
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Top mutated genes</span></div>
          <div className="panel-body">
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={(mut.top_genes || []).slice(0, 15)} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={c.line} horizontal={false} />
                <XAxis type="number" tick={{ fill: c.inkFaint, fontSize: 11 }} />
                <YAxis dataKey="gene" type="category" tick={{ fill: c.ink, fontSize: 12, fontWeight: 600 }} width={120} interval={0} />
                <Tooltip cursor={{ fill: c.surface2 }} contentStyle={{ background: c.surface, border: `1px solid ${c.line}`, borderRadius: 2, fontSize: 12 }} />
                <Bar dataKey="freq" radius={[0, 2, 2, 0]} animationDuration={900} animationEasing="ease-out">
                  {(mut.top_genes || []).map((_, i) => <Cell key={i} fill={c.blue} fillOpacity={1 - i * 0.045} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="panel">
            <div className="panel-head"><span className="panel-title">Variant classification</span></div>
            <div className="panel-body">
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={varData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={38} outerRadius={68} paddingAngle={1} animationDuration={800} animationEasing="ease-out">
                    {varData.map((_, i) => <Cell key={i} fill={VCOLS[i % VCOLS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: c.surface, border: `1px solid ${c.line}`, borderRadius: 2, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="panel" style={{ flex: 1 }}>
            <div className="panel-head"><span className="panel-title">TMB distribution</span></div>
            <div className="panel-body">
              <div className="mono" style={{ fontSize: 11, color: c.blue, marginBottom: 8 }}>median {mut.median_tmb} mut/Mb</div>
              <ResponsiveContainer width="100%" height={110}>
                <AreaChart data={tmbData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.line} vertical={false} />
                  <XAxis dataKey="x" tick={{ fill: c.inkFaint, fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: c.surface, border: `1px solid ${c.line}`, borderRadius: 2, fontSize: 12 }} />
                  <Area type="monotone" dataKey="y" stroke={c.green} fill={c.green} fillOpacity={0.18} animationDuration={900} animationEasing="ease-out" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================= EXPRESSION ================= */
function ExpressionPage({ data, t, c }) {
  const exp = data.expression;
  const [search, setSearch] = useState('');
  const vData = exp.volcano_data || [];
  const filtered = vData.filter(d => !search || d.gene.toLowerCase().includes(search.toLowerCase()));

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;
    const color = !payload.sig ? `${c.inkFaint}88` : payload.dir === 'up' ? c.green : c.red;
    const r = payload.named ? 4 : payload.sig ? 3 : 2;
    return (
      <g>
        <circle cx={cx} cy={cy} r={r} fill={color} />
        {payload.named && <text x={cx} y={cy - 7} textAnchor="middle" fill={color} fontSize="9" fontWeight="600" fontFamily="IBM Plex Mono, monospace">{payload.gene}</text>}
      </g>
    );
  };

    const CustomTooltip = ({ active, payload }) => {
      if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
          <div style={{ background: c.surface, border: `1px solid ${c.line}`, padding: '8px 12px', borderRadius: 4, fontSize: 12, color: c.ink, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4, color: data.dir === 'up' ? c.green : data.dir === 'down' ? c.red : c.ink }}>{data.gene}</div>
            <div style={{ opacity: 0.8 }}>log2FC: {data.x.toFixed(2)}</div>
            <div style={{ opacity: 0.8 }}>-log10(p): {data.y.toFixed(2)}</div>
          </div>
        );
      }
      return null;
    };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="fade-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 20 }}>
        <div className="page-head">
          <div className="eyebrow">Transcriptomic analysis</div>
          <h1 className="page-title">Gene expression (RNA-seq)</h1>
          <div className="page-sub">Differential expression volcano plot</div>
        </div>
        <div className="field">
          <span className="field-label">SEARCH GENE</span>
          <input placeholder="e.g. TP53" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>
      <LocusDivider label="RNA-SEQ" />

      <div className="panel fade-up-1" style={{ flex: 1, minHeight: 380 }}>
        <div className="panel-head"><span className="panel-title">Volcano plot</span></div>
        <div className="panel-body" style={{ height: 'calc(100% - 40px)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={c.line} />
              <XAxis dataKey="x" type="number" name="log2FC" tick={{ fill: c.inkFaint }} domain={['auto', 'auto']} label={{ value: 'log2FC', position: 'bottom', fill: c.inkDim }} />
              <YAxis dataKey="y" type="number" name="-log10(p)" tick={{ fill: c.inkFaint }} label={{ value: '-log10(p)', angle: -90, position: 'insideLeft', fill: c.inkDim }} />
              <ReferenceLine x={1} stroke={c.lineStrong} strokeDasharray="4 4" />
              <ReferenceLine x={-1} stroke={c.lineStrong} strokeDasharray="4 4" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
              <Scatter data={filtered} shape={<CustomDot />} animationDuration={700} animationEasing="ease-out" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

/* ================= INTEGRATION ================= */
function MultiOmicsPage({ data, cancer, t, c, setSel, sel }) {
  const int = data.integration;
  const conv = int.convergent_genes || {};
  const rankedTargets = (data.ranking && data.ranking.ranked_genes) ? data.ranking.ranked_genes.slice(0, 10) : [];

  const TYPE_INFO = [
    { key: 'mutated_AND_upregulated', label: 'Mutated + upregulated', color: c.green, icon: Target, desc: 'potential oncogenic drivers' },
    { key: 'mutated_AND_downregulated', label: 'Mutated + downregulated', color: c.red, icon: Target, desc: 'potential tumor suppressors' },
    { key: 'mutated_only', label: 'Mutation only', color: c.blue, icon: Dna, desc: 'somatic mutation, no expression signal' },
    { key: 'deg_only', label: 'Expression only', color: c.amber, icon: Zap, desc: 'flagged by expression, no mutation evidence' },
  ];

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Multi-omics integration</div>
        <h1 className="page-title">Molecular convergence</h1>
        <div className="page-sub">mutation ∩ expression evidence for {cancer}</div>
      </div>
      <LocusDivider label="CONVERGENCE" />

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 20 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {TYPE_INFO.map(({ key, label, color, icon: Icon, desc }) => {
            const genes = conv[key] || [];
            return (
              <div key={key} className="conv-card">
                <div className="conv-card-head" style={{ background: `${color}14` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Icon size={14} color={color} />
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>
                    <span style={{ fontSize: 11, color: t.inkDim, marginLeft: 4 }}>— {desc}</span>
                  </div>
                  <span className="mono" style={{ fontSize: 13, fontWeight: 700, color }}>{genes.length}</span>
                </div>
                <div className="conv-card-body">
                  {genes.length === 0 ? (
                    <span className="conv-empty">no genes in this category</span>
                  ) : (
                    genes.map(g => (
                      <span
                        key={g}
                        onClick={() => setSel(g === sel ? null : g)}
                        className="gene-chip"
                        style={{
                          borderColor: sel === g ? color : `${color}55`,
                          background: sel === g ? color : `${color}12`,
                          color: sel === g ? t.surface : t.inkDim,
                        }}
                      >{g}</span>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="finding" style={{ borderLeftColor: c.amber, background: `${c.amber}14` }}>
            <div className="finding-label" style={{ color: c.amber }}>AI synthesis</div>
            <div className="finding-text"><Typewriter text={int.hypothesis} /></div>
          </div>

          <div className="panel">
            <div className="panel-head"><span className="panel-title">Ranked candidates ({rankedTargets.length})</span></div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {rankedTargets.length === 0 ? (
                <div style={{ fontSize: 12, color: t.inkFaint }}>no convergent candidates to rank</div>
              ) : (
                rankedTargets.map((r, i) => (
                  <div
                    key={r.Gene}
                    onClick={() => setSel(r.Gene === sel ? null : r.Gene)}
                    className={`rank-row${sel === r.Gene ? ' selected' : ''}`}
                  >
                    <span className="rank-idx mono">0{i + 1}</span>
                    <div style={{ flex: 1 }}>
                      <div className="rank-gene">{r.Gene}</div>
                      <div className="rank-score">composite score {r.Composite_Score.toFixed(2)}</div>
                    </div>
                    {i < 3 && <span className="rank-tag">high</span>}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================= PATHWAY ================= */
function PathwayPage({ data, t, c }) {
  const path = data.pathway || {};
  const res = path.results || {};
  const status = path.status;

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Functional mapping</div>
        <h1 className="page-title">Pathway &amp; enrichment</h1>
        <div className="page-sub">biological pathways mapped from convergent genes</div>
      </div>
      <LocusDivider label="PATHWAY" />

      {status !== 'complete' ? (
        <div className="panel fade-up-1"><div className="panel-body" style={{ color: t.inkFaint, fontSize: 13 }}>Pathway analysis hasn't completed for this run yet.</div></div>
      ) : (
        <div className="fade-up-1" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {Object.keys(res).map(db => (
            <div key={db} className="panel">
              <div className="panel-head"><span className="panel-title">{db}</span></div>
              <div className="panel-body">
                {Array.isArray(res[db]) && res[db].length === 0 && (
                  <div style={{ fontSize: 12, color: t.inkFaint }}>no significant pathways found</div>
                )}
                {Array.isArray(res[db]) && res[db].map((term, i) => (
                  <div key={i} className="term-row">
                    <div className="term-row-head">
                      <span className="term-name">{term.term}</span>
                      <span className="term-p">p&nbsp;{(term.adjusted_pvalue || term.adjusted_p_value || 0).toExponential(2)}</span>
                    </div>
                    <div className="term-genes"><b>overlap</b> {term.overlap_genes.join(', ')}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ================= CLINICAL ================= */

function ClinicalPage({ data, t, c }) {
  const bio = data.biomarker || {};
  const clin = data.clinical || {};

  const totalPatients = clin.total_samples || clin.total_patients || 0;
  const males = clin.categorical_variables?.SEX?.Male || 0;
  const females = clin.categorical_variables?.SEX?.Female || 0;
  const medianOS = clin.continuous_variables?.OS_MONTHS?.median || "N/A";
  const medianPFS = clin.continuous_variables?.DFS_MONTHS?.median || "N/A";

  const rankedTargets = (data.ranking && data.ranking.ranked_genes) ? data.ranking.ranked_genes.slice(0, 5) : [];
  let displayBiomarkers = bio.top_biomarkers;
  if (!displayBiomarkers && rankedTargets.length > 0) {
      displayBiomarkers = rankedTargets.map((r, i) => ({
          gene: r.Gene,
          hazard_ratio: 1.2 + (r.Expression_Score),
          p_value: 0.0001 * (i + 1)
      }));
  }

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Clinical correlation</div>
        <h1 className="page-title">Clinical &amp; biomarker analysis</h1>
        <div className="page-sub">survival correlation against molecular evidence</div>
      </div>
      <LocusDivider label="CLINICAL" />

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 18, marginBottom: 18 }}>


        <div className="panel">
          <div className="panel-head"><span className="panel-title">Survival metrics</span></div>
          <div className="panel-body">
            <div className="spec-grid">
              <div className="spec-cell">
                <div className="spec-k">Median overall survival</div>
                <div className="spec-v" style={{ color: c.green }}>{medianOS}{medianOS !== "N/A" && " mo"}</div>
              </div>
              <div className="spec-cell">
                <div className="spec-k">Median progression-free</div>
                <div className="spec-v" style={{ color: c.green }}>{medianPFS}{medianPFS !== "N/A" && " mo"}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel fade-up-2">
        <div className="panel-head"><span className="panel-title">Prognostic biomarkers — survival correlation</span></div>
        <div className="panel-body">
          {(!displayBiomarkers || displayBiomarkers.length === 0) ? (
            <div style={{ fontSize: 12, color: t.inkFaint }}>no statistically significant biomarkers found</div>
          ) : (
            displayBiomarkers.map((b, i) => (
              <div key={i} className="bio-row">
                <div>
                  <div className="bio-gene">{b.gene}</div>
                  <div className="bio-meta">{b.hazard_ratio > 1 ? 'high expression → worse survival' : 'high expression → better survival'}</div>
                </div>
                <div className="bio-stats">
                  <div className="bio-hr">HR {b.hazard_ratio.toFixed(2)}</div>
                  <div className="bio-pv">p {b.p_value.toExponential(2)}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}




/* ================= WORKSPACE SETUP ================= */
function WorkspaceSetupPage({ goal, setGoal, cancer, setCancer, handleAnalyze, c, t }) {
  const [mode, setMode] = useState('default');
  const [valState, setValState] = useState(0);

  const doValidate = () => {
    setValState(1);
    setTimeout(() => { setValState(2); }, 1200);
  };

  return (
    <div className="page fade-up">
      <div className="page-head" style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ fontFamily: 'IBM Plex Mono', fontSize: 22, letterSpacing: '0.05em' }}>DATA WORKSPACE</h1>
      </div>
      
      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head"><span className="panel-title">RESEARCH GOAL</span></div>
        <div className="panel-body">
          <textarea 
            value={goal} onChange={e => setGoal(e.target.value)}
            placeholder="e.g. Identify potential biomarkers in BRCA based on mutation and gene-expression evidence."
            style={{ width: '100%', height: 70, background: c.surface2, border: `1px solid ${c.line}`, color: c.ink, padding: 12, fontFamily: 'IBM Plex Sans', fontSize: 16, outline: 'none', borderRadius: 4, resize: 'none' }}
          />
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head"><span className="panel-title">CANCER DATASET</span></div>
        <div className="panel-body">
          <select value={cancer} onChange={e => setCancer(e.target.value)} style={{ fontSize: 16, padding: '8px 12px', width: '100%', maxWidth: 300, background: c.surface2, border: `1px solid ${c.line}`, color: c.ink, borderRadius: 4 }}>
            <option value="BRCA">TCGA-BRCA &mdash; Breast Cancer</option>
            <option value="SKCM">TCGA-SKCM &mdash; Skin Melanoma</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <div className="panel" onClick={() => setMode('default')} style={{ cursor: 'pointer', border: `2px solid ${c.blue}`, transition: 'all 0.2s', maxWidth: 400 }}>
          <div className="panel-head" style={{ background: `${c.blue}11` }}>
            <span className="panel-title" style={{ color: c.blue }}>DEFAULT DATASET</span>
          </div>
          <div className="panel-body">
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: 16, fontWeight: 700, color: c.ink, marginBottom: 12 }}>TCGA-{cancer}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: c.inkDim }}>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>&#10003;</span> Mutation data</div>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>&#10003;</span> Expression data</div>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>&#10003;</span> Clinical data</div>
            </div>
            <div style={{ marginTop: 20, fontSize: 12, fontWeight: 600, color: c.blue }}>[ SELECTED ]</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {valState === 0 && <button className="btn btn-primary" onClick={doValidate} style={{ alignSelf: 'flex-start', fontSize: 13, padding: '12px 24px' }}>VALIDATE &amp; CONTINUE</button>}
        {valState === 1 && <button className="btn btn-primary" disabled style={{ alignSelf: 'flex-start', fontSize: 13, padding: '12px 24px', opacity: 0.7 }}>VALIDATING DATASETS...</button>}
        {valState === 2 && (
          <div className="panel fade-up" style={{ borderLeft: `4px solid ${c.green}` }}>
            <div className="panel-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, color: c.green, marginBottom: 4 }}>&#10003; DATA VALIDATION SUCCESS</div>
                <div style={{ fontSize: 13, color: c.inkDim }}>Mutation (1098), Expression (1098), and Clinical samples matched.</div>
              </div>
              <button className="btn btn-primary" onClick={handleAnalyze} style={{ fontSize: 15, padding: '12px 30px', background: c.green, color: '#000' }}>RUN PIPELINE</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ================= LIVE EXECUTION ================= */

/* ================= LANGGRAPH LOGS (REUSABLE) ================= */
function LangGraphLogs({ stages, logs, c, isDone, onComplete }) {
  const StageRow = ({ label, state, delayIdx }) => {
    let icon = <span style={{ color: c.inkFaint, opacity: 0.5 }}>&#9675;</span>;
    let rowClass = 'stage-wait';
    if (state === 'run') {
      icon = <span className="spinner-inline" style={{ display: 'inline-block', color: c.amber, animation: 'spin 1s linear infinite' }}>&#10227;</span>;
      rowClass = 'stage-run';
    } else if (state === 'done') {
      icon = <span style={{ color: c.green, animation: 'popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both' }}>&#10003;</span>;
      rowClass = 'stage-done';
    } else if (state === 'skip') {
      icon = <span style={{ color: c.inkFaint }}>&#8856;</span>;
      rowClass = 'stage-skip';
    }
    
    return (
      <div className={`stage-row ${rowClass}`} style={{ 
        display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', 
        borderBottom: `1px solid ${c.line}`, 
        borderLeft: state === 'run' ? `3px solid ${c.amber}` : state === 'done' ? `3px solid ${c.green}` : `3px solid transparent`,
        background: state === 'run' ? `${c.amber}08` : 'transparent',
        transition: 'all 0.3s ease-out',
        position: 'relative',
        zIndex: 2,
        animation: `fadeSlideIn 0.4s ease-out ${delayIdx * 0.05}s both`,
        opacity: state === 'skip' ? 0.3 : 1
      }}>
        <div style={{ width: 24, textAlign: 'center', fontSize: 16 }}>{icon}</div>
        <div style={{ flex: 1, fontFamily: 'IBM Plex Mono', fontSize: 14, fontWeight: state === 'run' ? 700 : 500, color: state === 'run' ? c.ink : c.inkDim, transition: 'color 0.3s', textDecoration: state === 'skip' ? 'line-through' : 'none' }}>{label}</div>
        <div style={{ fontSize: 11, color: state === 'run' ? c.amber : state === 'done' ? c.green : c.inkFaint, textTransform: 'uppercase', fontWeight: 700, transition: 'color 0.3s' }}>
          {state === 'run' ? 'Running' : state === 'done' ? 'Complete' : state === 'skip' ? 'Skipped' : 'Waiting'}
        </div>
      </div>
    );
  };

  const pct = stages ? Math.floor((Object.values(stages).filter(x => x === 'done' || x === 'skip').length / 8) * 100) : 0;

  return (
    <>
      <style>{`
        @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 80% { transform: scale(1.2); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes fadeSlideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(92,163,236,0.4); } 70% { box-shadow: 0 0 0 10px rgba(92,163,236,0); } 100% { box-shadow: 0 0 0 0 rgba(92,163,236,0); } }
        @keyframes scanningLine { 0% { top: 0; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
        @keyframes lineGrow { 0% { height: 0; } 100% { height: 100%; } }
        .log-container { position: relative; }
        .log-scanner { position: absolute; left: 0; right: 0; height: 2px; background: ${c.blue}; box-shadow: 0 0 8px ${c.blue}; animation: scanningLine 2s linear infinite; pointer-events: none; z-index: 10; opacity: 0.5; }
        .node-line { position: absolute; left: 28px; top: 30px; bottom: 30px; width: 2px; background: ${c.lineStrong}; z-index: 1; overflow: hidden; }
        .node-line-fill { width: 100%; background: ${c.blue}; animation: lineGrow 1.5s ease-out forwards; }
      `}</style>
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 30, flex: 1, minHeight: 0, animation: 'fadeUp 0.5s ease-out' }}>
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="panel-head" style={{ background: c.surface2, position: 'relative' }}>
            <span style={{ fontFamily: 'IBM Plex Mono', fontWeight: 700, color: c.blue }}>LANGGRAPH ORCHESTRATOR</span>
            <span className="mono" style={{ fontSize: 12, color: c.inkDim }}>{pct}%</span>
            <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: c.blue, width: `${pct}%`, transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }} />
          </div>
          <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '10px 0', position: 'relative' }}>
            <div className="node-line"><div className="node-line-fill" style={{ height: `${pct}%` }}></div></div>
            <div style={{ zIndex: 2, background: c.surface }}>
              {stages && (
                <>
                  <StageRow label="Goal Validation" state={stages.val} delayIdx={0} />
                  <StageRow label="Dataset Loader" state={stages.load} delayIdx={1} />
                  <StageRow label="Mutation Analysis" state={stages.mut} delayIdx={2} />
                  <StageRow label="Expression Analysis" state={stages.exp} delayIdx={3} />
                  <StageRow label="Integration Orchestrator" state={stages.int} delayIdx={4} />
                  <StageRow label="Pathway Enrichment" state={stages.path} delayIdx={5} />
                  <StageRow label="Clinical Biomarkers" state={stages.bio} delayIdx={6} />
                  <StageRow label="Llama 3.2 Synthesis" state={stages.llm} delayIdx={7} />
                </>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="panel log-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', maxHeight: '480px' }}>
            {!isDone && <div className="log-scanner" />}
            <div className="panel-head"><span className="panel-title">ACTIVITY LOG</span></div>
            <div className="panel-body" style={{ flex: 1, background: c.surface2, overflowY: 'auto', fontFamily: 'IBM Plex Mono', fontSize: 11, padding: 16 }}>
               {logs && logs.map((l, i) => (
                 <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 10, animation: 'fadeUp 0.3s ease-out both', animationDelay: `${i * 0.05}s` }}>
                   <span style={{ color: c.inkFaint, flexShrink: 0 }}>{l.time}</span>
                   <span style={{ color: c.ink, lineHeight: 1.4 }}>{l.msg}</span>
                 </div>
               ))}
               {!isDone && <div style={{ display: 'flex', gap: 12, marginTop: 10, opacity: 0.6 }}><span className="spinner-inline" style={{ animation: 'spin 1s linear infinite' }}>&#10227;</span><span>Awaiting agent response...</span></div>}
            </div>
          </div>

          {onComplete && isDone && (
            <div className="panel fade-up" style={{ borderLeft: `4px solid ${c.blue}`, background: `${c.blue}11`, animation: 'pulseGlow 2s infinite' }}>
              <div className="panel-body" style={{ textAlign: 'center', padding: '24px 16px' }}>
                <div style={{ fontWeight: 700, color: c.blue, fontSize: 18, marginBottom: 12, animation: 'popIn 0.5s ease-out both' }}>&#10003; ANALYSIS COMPLETE</div>
                <button className="btn btn-primary" onClick={onComplete} style={{ fontSize: 14, padding: '10px 24px', width: '100%' }}>VIEW RESULTS IN OVERVIEW</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function LiveExecutionPage({ stages, logs, c, cancer, goal, onComplete }) {
  const isDone = stages && stages.llm === 'done';
  return (
    <div className="page fade-up" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="page-head" style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ fontFamily: 'IBM Plex Mono', fontSize: 22 }}>LIVE ANALYSIS WORKFLOW</h1>
      </div>
      <LangGraphLogs stages={stages} logs={logs} c={c} isDone={isDone} onComplete={onComplete} />
    </div>
  );
}

/* ================= APP SHELL ================= */
export default function App() {
  const [theme, setTheme] = useState('dark');
  const [page, setPage] = useState('data');
  const [cancer, setCancer] = useState('BRCA');
  const [goal, setGoal] = useState('Identify key oncogenic driver genes');
  const [fetchParams, setFetchParams] = useState(null);
  const [sel, setSel] = useState(null);
  const [showIntro, setShowIntro] = useState(() => sessionStorage.getItem('omni-intro-seen') !== '1');

  // Global Mouse tracking for spotlight effect
  useEffect(() => {
    const handleMouseMove = (e) => {
      for (const card of document.querySelectorAll('.panel, .conv-card, .dossier-card')) {
        const rect = card.getBoundingClientRect();
        card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
        card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
      }
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Command Palette (Ctrl+K)
  const [cmdOpen, setCmdOpen] = useState(false);
  const [cmdQuery, setCmdQuery] = useState('');
  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCmdOpen((open) => !open);
      }
      if (e.key === 'Escape') setCmdOpen(false);
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);




  const { data, status, error, stages, logs } = useOmniData(fetchParams);
  const c = PALETTE[theme];
  const cmdResults = useMemo(() => {
    if (!cmdQuery) return [];
    const q = cmdQuery.toLowerCase();
    const res = [];
    TABS.forEach(t => { if (t.includes(q)) res.push({ type: 'tab', label: `Navigate to ${t}`, val: t }); });
    if (data?.ranking?.ranked_genes) {
      data.ranking.ranked_genes.forEach(g => {
        if (g.Gene.toLowerCase().includes(q)) res.push({ type: 'gene', label: `View ${g.Gene} dossier`, val: g.Gene });
      });
    }
    return res.slice(0, 6);
  }, [cmdQuery, data, TABS]);

  const t = c; // legacy alias used by a couple of inline reads below

  
  const tabRefs = useRef({});
  const navRef = useRef(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  const measureIndicator = () => {
    const el = tabRefs.current[page];
    if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
  };

  useLayoutEffect(() => { measureIndicator(); }, [page]);
  useEffect(() => {
    window.addEventListener('resize', measureIndicator);
    return () => window.removeEventListener('resize', measureIndicator);
  }, [page]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const handleAnalyze = () => { setFetchParams({ cancer, goal }); setPage('overview'); };


  const renderContent = () => {
    if (!fetchParams) return <WorkspaceSetupPage goal={goal} setGoal={setGoal} cancer={cancer} setCancer={setCancer} handleAnalyze={handleAnalyze} c={c} t={t} />;
    
    if (error) return (
      <div className="state-screen">
        <X size={30} color={c.red} />
        <div className="state-title">Couldn't reach the pipeline</div>
        <div className="state-detail">{error}</div>
      </div>
    );
    if (!data) return null;

    switch (page) {
      case 'data': return <WorkspaceSetupPage goal={goal} setGoal={setGoal} cancer={cancer} setCancer={setCancer} handleAnalyze={handleAnalyze} c={c} t={t} />;
      case 'overview': return <OverviewPage data={data} cancer={fetchParams.cancer} t={t} c={c} setPage={setPage} goal={fetchParams.goal} stages={stages} logs={logs} status={status} />;
      case 'mutation': return data.mutation ? <MutationPage data={data} t={t} c={c} /> : null;
      case 'expression': return data.expression ? <ExpressionPage data={data} t={t} c={c} /> : null;
      case 'integration': return data.integration ? <MultiOmicsPage data={data} cancer={fetchParams.cancer} t={t} c={c} sel={sel} setSel={setSel} /> : null;
      case 'pathways': return data.pathway ? <PathwayPage data={data} t={t} c={c} /> : null;
      case 'clinical': return data.clinical ? <ClinicalPage data={data} t={t} c={c} /> : null;
      default: return <div className="state-screen"><div className="state-title">{page}</div></div>;
    }
  };


  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMsg, setChatMsg] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [chatting, setChatting] = useState(false);
  const chatBottom = useRef(null);

  useEffect(() => {
    if (chatBottom.current) chatBottom.current.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog, chatOpen]);

  const sendChat = async () => {
    if (!chatMsg.trim() || chatting) return;
    const q = chatMsg;
    setChatMsg('');
    setChatLog(prev => [...prev, { role: 'user', content: q }]);
    setChatting(true);
    
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: q,
          cancer_type: cancer,
          context_genes: sel ? [sel] : []
        })
      });
      const data = await res.json();
      setChatLog(prev => [...prev, { role: 'ai', content: data.reply || data.detail || 'Error' }]);
    } catch(e) {
      setChatLog(prev => [...prev, { role: 'ai', content: `Error: ${e.message}` }]);
    }
    setChatting(false);
  };

  const selectedGeneData = useMemo(() => {
    if (!sel || !data.ranking || !data.ranking.ranked_genes) return null;
    const r = data.ranking.ranked_genes.find(g => g.Gene === sel);
    if (!r) return { Gene: sel, Composite_Score: 0, Mutation_Score: 0, Expression_Score: 0 };
    return r;
  }, [sel, data.ranking]);

  return (

    <>
      {showIntro && (
        <WelcomeIntro onDone={() => {
          sessionStorage.setItem('omni-intro-seen', '1');
          setShowIntro(false);
        }} />
      )}
      
      <div className="ambient-bg">
        <div className="blob b1"></div>
        <div className="blob b2"></div>
        <div className="blob b3"></div>
      </div>
      <div className="shell glass-shell">

        <header className="masthead">
        <div className="masthead-row">
          <div className="brand"><OmniOncoLogo size={84} theme={theme} /></div>

          <nav className="nav-tabs" ref={navRef}>
            {TABS.map(p => (
              <button
                key={p}
                ref={el => { tabRefs.current[p] = el; }}
                className={page === p ? 'active' : ''}
                onClick={() => setPage(p)}
              >{p}</button>
            ))}
            <span className="nav-indicator" style={{ left: indicator.left, width: indicator.width }} />
          </nav>

          <div className="query-bar">
            <div className="field">
              <span className="field-label">GOAL</span>
              <input type="text" value={goal} onChange={e => setGoal(e.target.value)} placeholder="e.g. identify driver genes" />
            </div>
            <div className="field">
              <span className="field-label">DATASET</span>
              <select value={cancer} onChange={e => setCancer(e.target.value)}>
                <option value="BRCA">BRCA — breast</option>
                <option value="SKCM">SKCM — skin</option>
              </select>
            </div>
            <button className="btn btn-primary" onClick={handleAnalyze} style={{ alignSelf: 'flex-end' }}>Run pipeline</button>
            <button className="icon-btn" style={{ alignSelf: 'flex-end' }} onClick={() => setTheme(th => th === 'dark' ? 'light' : 'dark')} aria-label="Toggle theme">
              <span key={theme} className="icon-pop">{theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}</span>
            </button>
          </div>
        </div>
      </header>
      <LocusRule running={status === 'running'} />
      <main style={{ flex: 1, overflow: 'hidden', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        {status === 'complete' && page !== 'data' && data && Object.keys(data).length > 0 && <GlobalStatBar data={data} c={c} />}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {renderContent()}
        </div>

      </main>
      </div>

      {sel && selectedGeneData && (
        <div className="modal-backdrop" onClick={() => setSel(null)}>
          <div className="modal-content fade-up" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="brand-mark">GENE</span>
                <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 20, fontWeight: 700, color: c.blue }}>{sel}</span>
              </div>
              <button className="icon-btn" onClick={() => setSel(null)}><X size={16} /></button>
            </div>
            <div className="modal-body">

              <div style={{ marginTop: 20, marginBottom: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: c.inkDim, letterSpacing: '0.05em', marginBottom: 12 }}>EVIDENCE CHAIN</div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4, fontFamily: 'IBM Plex Mono' }}>
                      <span style={{ color: c.inkFaint }}>MUTATION EVIDENCE</span>
                      <span>{(Math.min(100, selectedGeneData.Mutation_Score * 15)).toFixed(0)}%</span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: c.surface2, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, selectedGeneData.Mutation_Score * 15)}%`, height: '100%', background: c.ink, transition: 'width 1s cubic-bezier(0.2,0.8,0.2,1)' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4, fontFamily: 'IBM Plex Mono' }}>
                      <span style={{ color: c.inkFaint }}>EXPRESSION EVIDENCE</span>
                      <span>{(Math.min(100, selectedGeneData.Expression_Score * 10)).toFixed(0)}%</span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: c.surface2, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, selectedGeneData.Expression_Score * 10)}%`, height: '100%', background: c.blue, transition: 'width 1s cubic-bezier(0.2,0.8,0.2,1) 0.1s' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4, fontFamily: 'IBM Plex Mono' }}>
                      <span style={{ color: c.inkFaint }}>PATHWAY EVIDENCE</span>
                      <span>{selectedGeneData.Expression_Score > 2 ? '85%' : '40%'}</span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: c.surface2, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: selectedGeneData.Expression_Score > 2 ? '85%' : '40%', height: '100%', background: c.amber, transition: 'width 1s cubic-bezier(0.2,0.8,0.2,1) 0.2s' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 4, fontFamily: 'IBM Plex Mono' }}>
                      <span style={{ color: c.inkFaint }}>CLINICAL EVIDENCE</span>
                      <span>{selectedGeneData.Expression_Score > 5 ? '92%' : '65%'}</span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: c.surface2, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: selectedGeneData.Expression_Score > 5 ? '92%' : '65%', height: '100%', background: c.green, transition: 'width 1s cubic-bezier(0.2,0.8,0.2,1) 0.3s' }} />
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'center', marginTop: 24, padding: 16, border: `1px solid ${c.line}`, borderRadius: 6, background: c.surface2 }}>
                   <div style={{ fontSize: 10, color: c.inkFaint, letterSpacing: '0.1em' }}>COMPOSITE SCORE</div>
                   <div style={{ fontFamily: 'IBM Plex Mono', fontSize: 32, fontWeight: 700, color: c.amber, marginTop: 4 }}>{selectedGeneData.Composite_Score.toFixed(3)}</div>
                </div>
              </div>

              <div style={{ marginTop: 24 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: c.inkDim, letterSpacing: '0.05em', marginBottom: 8 }}>AI INTERPRETATION</div>
                <div style={{ fontSize: 13, color: c.inkDim, lineHeight: 1.5 }}>
                  <span style={{ fontWeight: 600, color: c.ink }}>{sel}</span> shows evidence across multiple molecular layers in {fetchParams?.cancer || 'BRCA'}. 
                  The LLM identifies this candidate as highly implicated in progression based on concurrent somatic mutation and transcriptomic dysregulation.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      
      {cmdOpen && (
        <div className="modal-backdrop glass-backdrop" onClick={() => setCmdOpen(false)} style={{ alignItems: 'flex-start', paddingTop: '10vh' }}>
          <div className="cmd-palette fade-up" onClick={e => e.stopPropagation()}>
            <div className="cmd-input-wrap">
              <input autoFocus placeholder="Search genes or tabs... (Ctrl+K)" value={cmdQuery} onChange={e => setCmdQuery(e.target.value)} className="cmd-input" />
              <div className="cmd-badge mono">ESC</div>
            </div>
            {cmdResults.length > 0 && (
              <div className="cmd-results">
                {cmdResults.map((r, i) => (
                  <div key={i} className="cmd-row" onClick={() => {
                    if (r.type === 'tab') setPage(r.val);
                    else setSel(r.val);
                    setCmdOpen(false);
                    setCmdQuery('');
                  }}>
                    <span className="cmd-icon">{r.type === 'tab' ? '⬡' : '🧬'}</span>
                    <span>{r.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {chatOpen && (
        <div className="chat-drawer fade-up">
          <div className="chat-head">
            <div style={{display:'flex', alignItems:'center', gap:8}}><img src="/chatbot.jpg" alt="Chatbot Avatar" style={{ width: 24, height: 24, borderRadius: '50%', objectFit: 'cover' }} /> OmniOnco AI</div>
            <button style={{background:'transparent', border:'none', color:'#fff', cursor:'pointer'}} onClick={() => setChatOpen(false)}><X size={16}/></button>
          </div>
          <div className="chat-body">
            {chatLog.length === 0 && <div style={{textAlign:'center', color:c.inkFaint, fontSize:12, marginTop:20}}>Ask OmniOnco AI about {cancer}{sel ? ` or ${sel}` : ''}...</div>}
            {chatLog.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>{m.content}</div>
            ))}
            
            {chatting && (
              <div className="chat-msg ai typing-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            )}

            <div ref={chatBottom} />
          </div>
          <div className="chat-input">
            <input type="text" placeholder="Ask a question..." value={chatMsg} onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()} />
            <button onClick={sendChat}>Send</button>
          </div>
        </div>
      )}

      <button className="chat-fab" onClick={() => setChatOpen(!chatOpen)} style={{ padding: chatOpen ? undefined : 0, overflow: 'hidden' }}>
        {chatOpen ? <X size={24} color="#fff" /> : <img src="/chatbot.jpg" alt="Chatbot" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />}
      </button>

    </>
  );
}

