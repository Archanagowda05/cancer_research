import { useState, useEffect, useMemo, useRef, useLayoutEffect } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, BarChart, Bar, Cell, PieChart, Pie,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  Target, Brain, Dna, Zap, X, Sun, Moon, FlaskConical
} from 'lucide-react';
import './App.css';
import WelcomeIntro from './WelcomeIntro';

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
      <span className="tag">A·C·G·T</span>
      <div className="bar"><span className="a" /><span className="c" /><span className="g" /><span className="t" /></div>
      {label && <span className="tag">{label}</span>}
    </div>
  );
}

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

function useOmniData(cancer, goal) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true); setError(null);
    const url = new URL(`${API_BASE}/full/${cancer}`);
    if (goal) url.searchParams.append('goal', goal);
    fetch(url)
      .then(r => { if (!r.ok) throw new Error('API Error'); return r.json(); })
      .then(d => { if (active) { setData(d); setLoading(false); } })
      .catch(e => { if (active) { setError(e.message); setLoading(false); } });
    return () => { active = false; };
  }, [cancer, goal]);

  return { data, loading, error };
}

/* ================= OVERVIEW ================= */
function OverviewPage({ data, cancer, t, c, setPage, goal }) {
  const { mutation: mut, expression: exp, integration: int, pathway: path, clinical: clin } = data;

  const stats = [
    { label: 'Patients', value: mut.total_patients, color: c.ink },
    { label: 'Mutated genes', value: mut.all_mutated_genes?.length || 500, color: c.ink },
    { label: 'DEGs', value: exp.significant_degs, color: c.blue },
    { label: 'Upregulated', value: exp.upregulated_count, color: c.green },
    { label: 'Downregulated', value: exp.downregulated_count, color: c.red },
  ];

  const steps = [
    'Data loaded', 'Mutation analysis', 'Expression analysis', 'Multi-omics integration',
    'Pathway analysis', 'Biomarker analysis', 'Llama 3.2 synthesis',
  ];
  const stepDone = [true, !!mut, !!exp, !!int, !!path, !!clin, !!int?.hypothesis];

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Case file — TCGA-{cancer}</div>
        <h1 className="page-title">AI Multi-Omics Agent for Breast &amp; Skin Cancer</h1>
        <div className="page-sub">Dataset <span className="dataset-chip">TCGA-{cancer}</span> · goal-driven agent, mutation + expression integration</div>
      </div>

      <div className="fade-up-1">
        <LocusDivider label="OVERVIEW" />
        <div className="stat-strip">
          {stats.map(s => (
            <div className="stat-cell" key={s.label}>
              <StatValue value={s.value} color={s.color} />
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="fade-up-2" style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 18 }}>
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Agent protocol</span>
            <Brain size={14} color={c.amber} />
          </div>
          <div className="panel-body">
            <div className="goal-plate">
              <div className="k">Research goal</div>
              <div className="v">&ldquo;{goal}&rdquo;</div>
            </div>
            <div className="protocol">
              {steps.map((label, i) => (
                <div className="protocol-step" key={label}>
                  <span className="protocol-num mono">SOP-{String(i + 1).padStart(2, '0')}</span>
                  <span className={`protocol-label${stepDone[i] ? '' : ' pending'}`}>{label}</span>
                  <span className={`protocol-status${stepDone[i] ? ' done' : ' pending'}`}>
                    {stepDone[i] ? 'done' : 'pending'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {int?.hypothesis && (
            <div className="finding">
              <div className="finding-label">AI synthesis</div>
              <div className="finding-text">{int.hypothesis}</div>
              <div className="finding-cite">generated by the integration agent</div>
            </div>
          )}
          <div className="panel">
            <div className="panel-head"><span className="panel-title">Go to</span></div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="btn btn-primary" onClick={() => setPage('integration')}>Integrated candidates</button>
              <button className="btn btn-ghost" onClick={() => setPage('pathways')}>Biological pathways</button>
              <button className="btn btn-ghost" onClick={() => setPage('clinical')}>Clinical &amp; biomarkers</button>
            </div>
          </div>
        </div>
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
        <div className="page-sub">{mut.total_mutations?.toLocaleString()} mutations across {mut.total_patients} patients</div>
      </div>
      <LocusDivider label="MAF" />

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 18 }}>
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Top mutated genes</span></div>
          <div className="panel-body">
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={(mut.top_genes || []).slice(0, 15)} layout="vertical" margin={{ left: 0, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={c.line} horizontal={false} />
                <XAxis type="number" tick={{ fill: c.inkFaint, fontSize: 11 }} />
                <YAxis dataKey="gene" type="category" tick={{ fill: c.ink, fontSize: 12, fontWeight: 600 }} width={80} />
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

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="fade-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 20 }}>
        <div className="page-head">
          <div className="eyebrow">Transcriptomic analysis</div>
          <h1 className="page-title">Gene expression (RNA-seq)</h1>
          <div className="page-sub">{exp.significant_degs} DEGs · {exp.upregulated_count} up · {exp.downregulated_count} down</div>
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
              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: c.surface, border: `1px solid ${c.line}`, borderRadius: 2, fontSize: 12 }} />
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
            <div className="finding-text">{int.hypothesis}</div>
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
                      <span className="term-p">p&nbsp;{term.adjusted_p_value.toExponential(2)}</span>
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

  return (
    <div className="page">
      <div className="page-head fade-up">
        <div className="eyebrow">Clinical correlation</div>
        <h1 className="page-title">Clinical &amp; biomarker analysis</h1>
        <div className="page-sub">survival correlation against molecular evidence</div>
      </div>
      <LocusDivider label="CLINICAL" />

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginBottom: 18 }}>
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Clinical summary</span></div>
          <div className="panel-body">
            <div className="spec-grid">
              <div className="spec-cell">
                <div className="spec-k">Total patients</div>
                <div className="spec-v" style={{ color: c.blue }}>{clin.total_patients || 0}</div>
              </div>
              <div className="spec-cell">
                <div className="spec-k">Male / female</div>
                <div className="spec-v">{(clin.demographics?.gender?.MALE || 0)} / {(clin.demographics?.gender?.FEMALE || 0)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><span className="panel-title">Survival metrics</span></div>
          <div className="panel-body">
            <div className="spec-grid">
              <div className="spec-cell">
                <div className="spec-k">Median overall survival</div>
                <div className="spec-v" style={{ color: c.green }}>{Math.round(clin.survival?.median_os_months || 0)} mo</div>
              </div>
              <div className="spec-cell">
                <div className="spec-k">Median progression-free</div>
                <div className="spec-v" style={{ color: c.green }}>{Math.round(clin.survival?.median_pfs_months || 0)} mo</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel fade-up-2">
        <div className="panel-head"><span className="panel-title">Prognostic biomarkers — survival correlation</span></div>
        <div className="panel-body">
          {(!bio.top_biomarkers || bio.top_biomarkers.length === 0) ? (
            <div style={{ fontSize: 12, color: t.inkFaint }}>no statistically significant biomarkers found</div>
          ) : (
            bio.top_biomarkers.map((b, i) => (
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

/* ================= APP SHELL ================= */
export default function App() {
  const [theme, setTheme] = useState('dark');
  const [page, setPage] = useState('overview');
  const [cancer, setCancer] = useState('BRCA');
  const [goal, setGoal] = useState('Identify key oncogenic driver genes');
  const [fetchParams, setFetchParams] = useState({ cancer: 'BRCA', goal: 'Identify key oncogenic driver genes' });
  const [sel, setSel] = useState(null);
  const [showIntro, setShowIntro] = useState(() => sessionStorage.getItem('omni-intro-seen') !== '1');

  const { data, loading, error } = useOmniData(fetchParams.cancer, fetchParams.goal);
  const c = PALETTE[theme];
  const t = c; // legacy alias used by a couple of inline reads below

  const TABS = ['overview', 'mutation', 'expression', 'integration', 'pathways', 'clinical'];
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

  const handleAnalyze = () => setFetchParams({ cancer, goal });

  const renderContent = () => {
    if (loading) return (
      <div className="state-screen">
        <DnaLoader cancer={cancer} c={c} />
        <div className="state-title">Running the pipeline for {cancer}…</div>
      </div>
    );
    if (error) return (
      <div className="state-screen">
        <X size={30} color={c.red} />
        <div className="state-title">Couldn't reach the pipeline</div>
        <div className="state-detail">{error} — confirm the API server is running on {API_BASE}.</div>
      </div>
    );
    if (!data) return null;

    switch (page) {
      case 'overview': return <OverviewPage data={data} cancer={cancer} t={t} c={c} setPage={setPage} goal={goal} />;
      case 'mutation': return <MutationPage data={data} t={t} c={c} />;
      case 'expression': return <ExpressionPage data={data} t={t} c={c} />;
      case 'integration': return <MultiOmicsPage data={data} cancer={cancer} t={t} c={c} sel={sel} setSel={setSel} />;
      case 'pathways': return <PathwayPage data={data} t={t} c={c} />;
      case 'clinical': return <ClinicalPage data={data} t={t} c={c} />;
      default: return (
        <div className="state-screen">
          <FlaskConical size={30} style={{ opacity: 0.3 }} />
          <div className="state-title">{page}</div>
        </div>
      );
    }
  };

  return (
    <>
      {showIntro && (
        <WelcomeIntro onDone={() => {
          sessionStorage.setItem('omni-intro-seen', '1');
          setShowIntro(false);
        }} />
      )}
      <div className="shell">
        <header className="masthead">
        <div className="masthead-row">
          <div className="brand">
            <span className="brand-mark">OMN</span>
            <span className="brand-name">OmniOnco <em>AI</em></span>
          </div>

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
      <LocusRule running={loading} />
      <main style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {renderContent()}
      </main>
      </div>
    </>
  );
}
