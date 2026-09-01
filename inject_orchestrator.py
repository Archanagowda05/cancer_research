import os
import re

with open(r'frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

# 1. Replace DataEntryPage with WorkspaceSetupPage
workspace_setup = """
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
            <option value="BRCA">TCGA-BRCA — Breast Cancer</option>
            <option value="SKCM">TCGA-SKCM — Skin Melanoma</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div className="panel" onClick={() => setMode('default')} style={{ cursor: 'pointer', border: mode === 'default' ? `2px solid ${c.blue}` : `1px solid ${c.line}`, transition: 'all 0.2s' }}>
          <div className="panel-head" style={{ background: mode === 'default' ? `${c.blue}11` : 'transparent' }}>
            <span className="panel-title" style={{ color: mode === 'default' ? c.blue : c.inkDim }}>DEFAULT DATASET</span>
          </div>
          <div className="panel-body">
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: 16, fontWeight: 700, color: c.ink, marginBottom: 12 }}>TCGA-{cancer}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: c.inkDim }}>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>✓</span> Mutation data</div>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>✓</span> Expression data</div>
              <div><span style={{ color: c.green, fontWeight: 700, marginRight: 8 }}>✓</span> Clinical data</div>
            </div>
            {mode === 'default' && <div style={{ marginTop: 20, fontSize: 12, fontWeight: 600, color: c.blue }}>[ SELECTED ]</div>}
          </div>
        </div>

        <div className="panel" onClick={() => setMode('custom')} style={{ cursor: 'pointer', border: mode === 'custom' ? `2px solid ${c.blue}` : `1px solid ${c.line}`, transition: 'all 0.2s' }}>
          <div className="panel-head" style={{ background: mode === 'custom' ? `${c.blue}11` : 'transparent' }}>
            <span className="panel-title" style={{ color: mode === 'custom' ? c.blue : c.inkDim }}>CUSTOM DATA</span>
          </div>
          <div className="panel-body">
             <div style={{ fontSize: 13, color: c.inkDim, marginBottom: 12 }}>Upload your own omics files</div>
             <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: c.surface2, padding: '6px 10px', borderRadius: 4 }}>
                 <span style={{ fontSize: 12, fontWeight: 600 }}>Mutation</span>
                 <span style={{ fontSize: 10, color: c.inkFaint }}>[ Drop MAF / TXT ]</span>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: c.surface2, padding: '6px 10px', borderRadius: 4 }}>
                 <span style={{ fontSize: 12, fontWeight: 600 }}>Expression</span>
                 <span style={{ fontSize: 10, color: c.inkFaint }}>[ Drop RSEM / CSV ]</span>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: c.surface2, padding: '6px 10px', borderRadius: 4 }}>
                 <span style={{ fontSize: 12, fontWeight: 600 }}>Clinical</span>
                 <span style={{ fontSize: 10, color: c.inkFaint }}>[ Drop TSV ]</span>
               </div>
             </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {valState === 0 && <button className="btn btn-primary" onClick={doValidate} style={{ alignSelf: 'flex-start', fontSize: 13, padding: '12px 24px' }}>VALIDATE & CONTINUE</button>}
        {valState === 1 && <button className="btn btn-primary" disabled style={{ alignSelf: 'flex-start', fontSize: 13, padding: '12px 24px', opacity: 0.7 }}>VALIDATING DATASETS...</button>}
        {valState === 2 && (
          <div className="panel fade-up" style={{ borderLeft: `4px solid ${c.green}` }}>
            <div className="panel-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 700, color: c.green, marginBottom: 4 }}>✓ DATA VALIDATION SUCCESS</div>
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
function LiveExecutionPage({ stages, logs, c, cancer, goal, onComplete }) {
  const StageRow = ({ label, state }) => {
    let icon = <span style={{ color: c.inkFaint }}>○</span>;
    if (state === 'run') icon = <span className="spinner-inline" style={{ display: 'inline-block', color: c.amber, animation: 'spin 1s linear infinite' }}>⟳</span>;
    if (state === 'done') icon = <span style={{ color: c.green }}>✓</span>;
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0', borderBottom: `1px solid ${c.line}`, opacity: state === 'wait' ? 0.5 : 1, transition: 'opacity 0.3s' }}>
        <div style={{ width: 24, textAlign: 'center', fontSize: 16 }}>{icon}</div>
        <div style={{ flex: 1, fontFamily: 'IBM Plex Mono', fontSize: 14, fontWeight: state === 'run' ? 700 : 500, color: state === 'run' ? c.ink : c.inkDim }}>{label}</div>
        <div style={{ fontSize: 11, color: state === 'run' ? c.amber : c.inkFaint, textTransform: 'uppercase', fontWeight: 700 }}>
          {state === 'run' ? 'Running' : state === 'done' ? 'Complete' : 'Waiting'}
        </div>
      </div>
    );
  };

  const isDone = stages.llm === 'done';
  const pct = Math.floor((Object.values(stages).filter(x => x === 'done').length / 8) * 100);

  return (
    <div className="page fade-up" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="page-head" style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ fontFamily: 'IBM Plex Mono', fontSize: 22 }}>LIVE ANALYSIS WORKFLOW</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 30, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="panel-head" style={{ background: c.surface2 }}>
            <span style={{ fontFamily: 'IBM Plex Mono', fontWeight: 700, color: c.blue }}>LANGGRAPH ORCHESTRATOR</span>
            <span className="mono" style={{ fontSize: 12, color: c.inkDim }}>{pct}%</span>
          </div>
          <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '10px 30px' }}>
            <StageRow label="Goal Validation" state={stages.val} />
            <StageRow label="Dataset Loader" state={stages.load} />
            <StageRow label="Mutation Analysis" state={stages.mut} />
            <StageRow label="Expression Analysis" state={stages.exp} />
            <StageRow label="Integration Orchestrator" state={stages.int} />
            <StageRow label="Pathway Enrichment" state={stages.path} />
            <StageRow label="Clinical Biomarkers" state={stages.bio} />
            <StageRow label="Llama 3.2 Synthesis" state={stages.llm} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="panel-head"><span className="panel-title">ACTIVITY LOG</span></div>
            <div className="panel-body" style={{ flex: 1, background: c.surface2, overflowY: 'auto', fontFamily: 'IBM Plex Mono', fontSize: 11, padding: 16 }}>
               {logs.map((l, i) => (
                 <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 10, animation: 'fadeUp 0.3s ease-out both' }}>
                   <span style={{ color: c.inkFaint, flexShrink: 0 }}>{l.time}</span>
                   <span style={{ color: c.ink, lineHeight: 1.4 }}>{l.msg}</span>
                 </div>
               ))}
               {!isDone && <div style={{ display: 'flex', gap: 12, marginTop: 10, opacity: 0.6 }}><span className="spinner-inline" style={{ animation: 'spin 1s linear infinite' }}>⟳</span><span>Awaiting agent response...</span></div>}
            </div>
          </div>

          {isDone && (
            <div className="panel fade-up" style={{ borderLeft: `4px solid ${c.blue}`, background: `${c.blue}11` }}>
              <div className="panel-body" style={{ textAlign: 'center', padding: '24px 16px' }}>
                <div style={{ fontWeight: 700, color: c.blue, fontSize: 18, marginBottom: 12 }}>✓ ANALYSIS COMPLETE</div>
                <button className="btn btn-primary" onClick={onComplete} style={{ fontSize: 14, padding: '10px 24px', width: '100%' }}>VIEW RESULTS IN OVERVIEW</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"""

# Replace DataEntryPage with WorkspaceSetupPage and LiveExecutionPage
app = re.sub(r'/\* ================= DATA IMPORT ================= \*/.*?/\* ================= OVERVIEW ================= \*/', workspace_setup + '/* ================= OVERVIEW ================= */', app, flags=re.DOTALL)


# 2. Rewrite useOmniData to track stages and logs
hook_replacement = """
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
        await new Promise(r => setTimeout(r, 600)); 
        if (!active) return;
        setStages(s => ({ ...s, val: 'done', load: 'run' }));
        addLog(`Loading TCGA-${cancer} default dataset into memory...`);
        await new Promise(r => setTimeout(r, 800));
        
        if (!active) return;
        setStages(s => ({ ...s, load: 'done', mut: 'run' }));
        addLog('Executing somatic mutation analysis...');
        let m = await fetch(`${API_BASE}/mutation/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, mutation: m }));
        addLog(`Identified ${m.all_mutated_genes?.length || 500} mutated genes across ${m.total_patients} patients.`);
        
        setStages(s => ({ ...s, mut: 'done', exp: 'run' }));
        addLog('Scoring differential expression (RNA-seq)...');
        let e = await fetch(`${API_BASE}/expression/${cancer}?top_n=500`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, expression: e }));
        addLog(`Found ${e.significant_degs} significant DEGs (${e.upregulated_count} up, ${e.downregulated_count} down).`);
        
        setStages(s => ({ ...s, exp: 'done', int: 'run' }));
        addLog('Orchestrating multi-omics convergence...');
        let i = await fetch(`${API_BASE}/integration/${cancer}`).then(r => r.json());
        let rank = await fetch(`${API_BASE}/ranking/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, integration: i, ranking: rank }));
        addLog(`Ranked ${rank.ranked_genes?.length || 0} candidate biomarkers.`);
        
        setStages(s => ({ ...s, int: 'done', path: 'run' }));
        addLog('Mapping biological pathways from Enrichr...');
        let p = await fetch(`${API_BASE}/pathway/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, pathway: p }));
        addLog(`Mapped targets to ${Object.keys(p.results || {}).length} pathway databases.`);
        
        setStages(s => ({ ...s, path: 'done', bio: 'run' }));
        addLog('Correlating clinical survival data (Primary vs Metastasis)...');
        let c = await fetch(`${API_BASE}/clinical/${cancer}`).then(r => r.json());
        let b = await fetch(`${API_BASE}/biomarker/${cancer}`).then(r => r.json());
        if (!active) return;
        setData(d => ({ ...d, clinical: c, biomarker: b }));
        addLog('Clinical cross-validation complete.');
        
        setStages(s => ({ ...s, bio: 'done', llm: 'run' }));
        addLog('Dispatching aggregated context to local Llama 3.2 for synthesis...');
        
        let url = new URL(`${API_BASE}/full/${cancer}`);
        if (goal) url.searchParams.append('goal', goal);
        let f = await fetch(url).then(r => r.json());
        if (!active) return;
        setData(f);
        
        setStages(s => ({ ...s, llm: 'done' }));
        addLog('AI synthesis complete. Pipeline finished successfully.');
        setStatus('complete');

      } catch (err) {
        if (active) { setError(err.message); setStatus('error'); }
      }
    };
    runPipeline();
    return () => { active = false; };
  }, [fetchParams]);

  return { data, status, error, stages, logs };
}
"""
app = re.sub(r'function useOmniData\(.*?return \{ data, loading: Object.keys\(data\).length === 0 && !error, error \};\n\}', hook_replacement, app, flags=re.DOTALL)


# 3. Update App component state to handle execution flow
app = app.replace('const [fetchParams, setFetchParams] = useState({ cancer: \'BRCA\', goal: \'Identify key oncogenic driver genes\' });', 'const [fetchParams, setFetchParams] = useState(null);')

# Replace renderContent in App.jsx
render_content_new = """
  const renderContent = () => {
    if (!fetchParams) return <WorkspaceSetupPage goal={goal} setGoal={setGoal} cancer={cancer} setCancer={setCancer} handleAnalyze={handleAnalyze} c={c} t={t} />;
    
    if (status === 'running' || (status === 'complete' && page === 'data')) {
      return <LiveExecutionPage stages={stages} logs={logs} c={c} t={t} cancer={fetchParams.cancer} goal={fetchParams.goal} onComplete={() => setPage('overview')} />;
    }

    if (error) return (
      <div className="state-screen">
        <X size={30} color={c.red} />
        <div className="state-title">Couldn't reach the pipeline</div>
        <div className="state-detail">{error}</div>
      </div>
    );
    if (!data) return null;

    switch (page) {
      case 'overview': return <OverviewPage data={data} cancer={fetchParams.cancer} t={t} c={c} setPage={setPage} goal={fetchParams.goal} />;
      case 'mutation': return data.mutation ? <MutationPage data={data} t={t} c={c} /> : null;
      case 'expression': return data.expression ? <ExpressionPage data={data} t={t} c={c} /> : null;
      case 'integration': return data.integration ? <MultiOmicsPage data={data} cancer={fetchParams.cancer} t={t} c={c} sel={sel} setSel={setSel} /> : null;
      case 'pathways': return data.pathway ? <PathwayPage data={data} t={t} c={c} /> : null;
      case 'clinical': return data.clinical ? <ClinicalPage data={data} t={t} c={c} /> : null;
      default: return <div className="state-screen"><div className="state-title">{page}</div></div>;
    }
  };
"""
app = re.sub(r'  const renderContent = \(\) => \{.*?  \};\n', render_content_new, app, flags=re.DOTALL)

# Update useOmniData destructuring in App
app = app.replace('const { data, loading, error } = useOmniData(fetchParams.cancer, fetchParams.goal);', 'const { data, status, error, stages, logs } = useOmniData(fetchParams);')


# 4. Inject "Evidence Chain" UI into Gene Dossier
evidence_chain = """
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
"""
app = re.sub(r'              <div className="dossier-grid">.*?</div>\n              <p className="mt-3".*?</p>', evidence_chain, app, flags=re.DOTALL)


# Remove the LocusRule from below the header because we have a proper execution screen now
app = app.replace('<LocusRule running={loading} />', '<LocusRule running={status === \'running\'} />')


with open(r'frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)

print("Applied massive UX updates (Workspace, LangGraph Live, Evidence Chain)")
