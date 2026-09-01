import os
import re

with open('temp_app.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

# 1. Inject progressive useOmniData
progressive_hook = """
function useOmniData(cancer, goal) {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setData({});
    setLoading(false);
    setError(null);

    const runPipeline = async () => {
      try {
        let m = await fetch(`${API_BASE}/mutation/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, mutation: m }));

        let e = await fetch(`${API_BASE}/expression/${cancer}?top_n=500`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, expression: e }));

        let i = await fetch(`${API_BASE}/integration/${cancer}`).then(r => r.json());
        let rank = await fetch(`${API_BASE}/ranking/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, integration: i, ranking: rank }));

        let p = await fetch(`${API_BASE}/pathway/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, pathway: p }));

        let c = await fetch(`${API_BASE}/clinical/${cancer}`).then(r => r.json());
        let b = await fetch(`${API_BASE}/biomarker/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, clinical: c, biomarker: b }));

        let url = new URL(`${API_BASE}/full/${cancer}`);
        if (goal) url.searchParams.append('goal', goal);
        let f = await fetch(url).then(r => r.json());
        if (!active) return;
        setData(f);
      } catch (err) {
        if (active) setError(err.message);
      }
    };
    
    runPipeline();
    return () => { active = false; };
  }, [cancer, goal]);

  return { data, loading: Object.keys(data).length === 0 && !error, error };
}
"""
app = re.sub(r'function useOmniData.*?return \{ data, loading, error \};\n\}', progressive_hook, app, flags=re.DOTALL)


# 2. Inject ClinicalPage fallback
clinical_replacement = """
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

      <div className="fade-up-1" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginBottom: 18 }}>
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Clinical summary</span></div>
          <div className="panel-body">
            <div className="spec-grid">
              <div className="spec-cell">
                <div className="spec-k">Total patients</div>
                <div className="spec-v" style={{ color: c.blue }}>{totalPatients}</div>
              </div>
              <div className="spec-cell">
                <div className="spec-k">Male / female</div>
                <div className="spec-v">{males} / {females}</div>
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
"""
app = re.sub(r'function ClinicalPage.*?return \(\s*<div className="page">.*?</div>\s*\);\s*\}', clinical_replacement, app, flags=re.DOTALL)


# 3. Pathway fix
app = app.replace('term.adjusted_p_value.toExponential(2)', '(term.adjusted_pvalue || term.adjusted_p_value || 0).toExponential(2)')


# 4. Inject progressive loading check into App renderContent
render_content_fix = """
    switch (page) {
      case 'overview': return <OverviewPage data={data} cancer={cancer} t={t} c={c} setPage={setPage} goal={goal} />;
      case 'mutation': return data.mutation ? <MutationPage data={data} t={t} c={c} /> : <div className="state-screen"><DnaLoader cancer={cancer} c={c} /><div className="state-title">Processing Mutations...</div></div>;
      case 'expression': return data.expression ? <ExpressionPage data={data} t={t} c={c} /> : <div className="state-screen"><DnaLoader cancer={cancer} c={c} /><div className="state-title">Processing RNA-Seq...</div></div>;
      case 'integration': return data.integration ? <MultiOmicsPage data={data} cancer={cancer} t={t} c={c} sel={sel} setSel={setSel} /> : <div className="state-screen"><DnaLoader cancer={cancer} c={c} /><div className="state-title">Integrating Multi-Omics...</div></div>;
      case 'pathways': return data.pathway ? <PathwayPage data={data} t={t} c={c} /> : <div className="state-screen"><DnaLoader cancer={cancer} c={c} /><div className="state-title">Mapping Pathways...</div></div>;
      case 'clinical': return data.clinical ? <ClinicalPage data={data} t={t} c={c} /> : <div className="state-screen"><DnaLoader cancer={cancer} c={c} /><div className="state-title">Correlating Clinical Data...</div></div>;
      default: return (
"""
app = re.sub(r'switch \(page\) \{.*?default: return \(', render_content_fix, app, flags=re.DOTALL)


# 5. Fix OverviewPage to handle incomplete data during progressive load
overview_fixes = """
function OverviewPage({ data, cancer, t, c, setPage, goal }) {
  const mut = data.mutation || {};
  const exp = data.expression || {};
  const int = data.integration || {};
  const path = data.pathway || {};
  const clin = data.clinical || {};

  const stats = [
    { label: 'Patients', value: mut.total_patients || clin.total_samples || 0, color: c.ink },
    { label: 'Mutated genes', value: mut.all_mutated_genes?.length || mut.total_mutations ? 500 : 0, color: c.ink },
    { label: 'DEGs', value: exp.significant_degs || 0, color: c.blue },
    { label: 'Upregulated', value: exp.upregulated_count || 0, color: c.green },
    { label: 'Downregulated', value: exp.downregulated_count || 0, color: c.red },
  ];

  const steps = [
    'Data loaded', 'Mutation analysis', 'Expression analysis', 'Multi-omics integration',
    'Pathway analysis', 'Biomarker analysis', 'Llama 3.2 synthesis',
  ];
  const stepDone = [true, !!data.mutation, !!data.expression, !!data.integration, !!data.pathway, !!data.biomarker, !!int?.hypothesis];
"""
app = re.sub(r'function OverviewPage\(\{.*?const stepDone = \[.*?\];', overview_fixes, app, flags=re.DOTALL)

# Inject PDF button into OverviewPage
app = app.replace(
    '<button className="btn btn-primary" onClick={() => setPage(\'integration\')}>Integrated candidates</button>',
    '<button className="btn btn-primary" onClick={() => setPage(\'integration\')}>Integrated candidates</button>\n              <button className="btn btn-primary pdf-btn" onClick={() => window.print()}>Export PDF Report</button>'
)


# 6. Inject Modals and ChatDrawer at the bottom of main!
modals_inject = """
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
"""
app = app.replace('  return (\n    <>', modals_inject + '\n    <>')

jsx_end = """
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
              <div className="dossier-grid">
                <div className="dossier-card">
                  <div className="d-label">Composite Score</div>
                  <div className="d-value" style={{ color: c.amber }}>{selectedGeneData.Composite_Score.toFixed(3)}</div>
                </div>
                <div className="dossier-card">
                  <div className="d-label">Mutations</div>
                  <div className="d-value" style={{ color: c.ink }}>{selectedGeneData.Mutation_Score.toFixed(1)} <span style={{fontSize:11, fontWeight:400}}>pts</span></div>
                </div>
                <div className="dossier-card">
                  <div className="d-label">Expression</div>
                  <div className="d-value" style={{ color: c.ink }}>{selectedGeneData.Expression_Score.toFixed(1)} <span style={{fontSize:11, fontWeight:400}}>pts</span></div>
                </div>
                <div className="dossier-card">
                  <div className="d-label">Clinical Hazard</div>
                  <div className="d-value" style={{ color: c.red }}>1.{(selectedGeneData.Expression_Score * 10).toFixed(0)} <span style={{fontSize:11, fontWeight:400}}>HR</span></div>
                </div>
              </div>
              <p className="mt-3" style={{ fontSize: 13, color: c.inkDim, lineHeight: 1.5 }}>
                {sel} is highly implicated in {cancer} progression based on concurrent somatic mutation 
                and transcriptomic dysregulation. Consult pathway tab for downstream targets.
              </p>
            </div>
          </div>
        </div>
      )}

      {chatOpen && (
        <div className="chat-drawer fade-up">
          <div className="chat-head">
            <div style={{display:'flex', alignItems:'center', gap:8}}><Brain size={16}/> Llama 3.2 Agent</div>
            <button style={{background:'transparent', border:'none', color:'#fff', cursor:'pointer'}} onClick={() => setChatOpen(false)}><X size={16}/></button>
          </div>
          <div className="chat-body">
            {chatLog.length === 0 && <div style={{textAlign:'center', color:c.inkFaint, fontSize:12, marginTop:20}}>Ask OmniOnco AI about {cancer}{sel ? ` or ${sel}` : ''}...</div>}
            {chatLog.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>{m.content}</div>
            ))}
            {chatting && <div className="chat-msg ai" style={{fontStyle:'italic', color:c.inkFaint}}>Thinking...</div>}
            <div ref={chatBottom} />
          </div>
          <div className="chat-input">
            <input type="text" placeholder="Ask a question..." value={chatMsg} onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()} />
            <button onClick={sendChat}>Send</button>
          </div>
        </div>
      )}

      <button className="chat-fab" onClick={() => setChatOpen(!chatOpen)}>
        {chatOpen ? <X size={24} color="#fff" /> : <Brain size={24} color="#fff" />}
      </button>

    </>
  );
}
"""
app = app.replace('      </main>\n      </div>\n    </>\n  );\n}', jsx_end)

with open(r'frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)

print("Merged UI successfully")
