import os
import re

file_path = r'frontend\src\App.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    app = f.read()

# 1. Global Stat Bar component to inject
global_stat_bar = """
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

"""

app = re.sub(r'(/\* ================= OVERVIEW ================= \*/)', global_stat_bar + r'\1', app)

main_replacement = """<main style={{ flex: 1, overflow: 'hidden', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        {status === 'complete' && page !== 'data' && data && Object.keys(data).length > 0 && <GlobalStatBar data={data} c={c} />}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {renderContent()}
        </div>"""
app = app.replace('<main style={{ flex: 1, overflow: \'hidden\', position: \'relative\' }}>\n        {renderContent()}', main_replacement)

# Remove old OverviewPage stats
app = re.sub(r'  const stats = \[\n.*?  \];\n', '', app, flags=re.DOTALL)
app = re.sub(r'        <div className="stat-strip">.*?        </div>\n', '', app, flags=re.DOTALL)

# Clean up redundant titles
app = re.sub(r'<div className="page-sub">.*?mutations across.*?patients</div>', '<div className="page-sub">Variant classifications & TMB distribution</div>', app)
app = re.sub(r'<div className="page-sub">.*?DEGs ·.*?up ·.*?down</div>', '<div className="page-sub">Differential expression volcano plot</div>', app)

# Remove clinical summary and fix layout
clinical_summary_remove = r'''        <div className="panel">\s*<div className="panel-head"><span className="panel-title">Clinical summary</span></div>\s*<div className="panel-body">\s*<div className="spec-grid">\s*<div className="spec-cell">\s*<div className="spec-k">Total patients</div>\s*<div className="spec-v" style={{ color: c\.blue }}>\{totalPatients\}</div>\s*</div>\s*<div className="spec-cell">\s*<div className="spec-k">Male / female</div>\s*<div className="spec-v">\{males\} / \{females\}</div>\s*</div>\s*</div>\s*</div>\s*</div>'''
app = re.sub(clinical_summary_remove, '', app, flags=re.DOTALL)
app = re.sub(r'<div className="fade-up-1" style={{ display: \'grid\', gridTemplateColumns: \'1fr 1fr\', gap: 18, marginBottom: 18 }}>', '<div className="fade-up-1" style={{ display: \'grid\', gridTemplateColumns: \'1fr\', gap: 18, marginBottom: 18 }}>', app)

live_execution_page = """
/* ================= LIVE EXECUTION ================= */
function LiveExecutionPage({ stages, logs, c, cancer, goal, onComplete }) {
  const StageRow = ({ label, state, delayIdx }) => {
    let icon = <span style={{ color: c.inkFaint, opacity: 0.5 }}>○</span>;
    let rowClass = 'stage-wait';
    if (state === 'run') {
      icon = <span className="spinner-inline" style={{ display: 'inline-block', color: c.amber, animation: 'spin 1s linear infinite' }}>⟳</span>;
      rowClass = 'stage-run';
    }
    if (state === 'done') {
      icon = <span style={{ color: c.green, animation: 'popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both' }}>✓</span>;
      rowClass = 'stage-done';
    }
    
    return (
      <div className={`stage-row ${rowClass}`} style={{ 
        display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', 
        borderBottom: `1px solid ${c.line}`, 
        borderLeft: state === 'run' ? `3px solid ${c.amber}` : state === 'done' ? `3px solid ${c.green}` : `3px solid transparent`,
        background: state === 'run' ? `${c.amber}08` : 'transparent',
        transition: 'all 0.3s ease-out',
        animation: `fadeSlideIn 0.4s ease-out ${delayIdx * 0.05}s both`
      }}>
        <div style={{ width: 24, textAlign: 'center', fontSize: 16 }}>{icon}</div>
        <div style={{ flex: 1, fontFamily: 'IBM Plex Mono', fontSize: 14, fontWeight: state === 'run' ? 700 : 500, color: state === 'run' ? c.ink : c.inkDim, transition: 'color 0.3s' }}>{label}</div>
        <div style={{ fontSize: 11, color: state === 'run' ? c.amber : state === 'done' ? c.green : c.inkFaint, textTransform: 'uppercase', fontWeight: 700, transition: 'color 0.3s' }}>
          {state === 'run' ? 'Running' : state === 'done' ? 'Complete' : 'Waiting'}
        </div>
      </div>
    );
  };

  const isDone = stages.llm === 'done';
  const pct = Math.floor((Object.values(stages).filter(x => x === 'done').length / 8) * 100);

  return (
    <div className="page fade-up" style={{ display: 'flex', flexDirection: 'column' }}>
      <style>{`
        @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 80% { transform: scale(1.2); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes fadeSlideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes pulseGlow { 0% { box-shadow: 0 0 0 0 rgba(92,163,236,0.4); } 70% { box-shadow: 0 0 0 10px rgba(92,163,236,0); } 100% { box-shadow: 0 0 0 0 rgba(92,163,236,0); } }
        @keyframes scanningLine { 0% { top: 0; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
        .log-container { position: relative; }
        .log-scanner { position: absolute; left: 0; right: 0; height: 2px; background: ${c.blue}; box-shadow: 0 0 8px ${c.blue}; animation: scanningLine 2s linear infinite; pointer-events: none; z-index: 10; opacity: 0.5; }
      `}</style>
      <div className="page-head" style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ fontFamily: 'IBM Plex Mono', fontSize: 22 }}>LIVE ANALYSIS WORKFLOW</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 30, flex: 1, minHeight: 0 }}>
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="panel-head" style={{ background: c.surface2, position: 'relative' }}>
            <span style={{ fontFamily: 'IBM Plex Mono', fontWeight: 700, color: c.blue }}>LANGGRAPH ORCHESTRATOR</span>
            <span className="mono" style={{ fontSize: 12, color: c.inkDim }}>{pct}%</span>
            <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: c.blue, width: `${pct}%`, transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }} />
          </div>
          <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '10px 0' }}>
            <StageRow label="Goal Validation" state={stages.val} delayIdx={0} />
            <StageRow label="Dataset Loader" state={stages.load} delayIdx={1} />
            <StageRow label="Mutation Analysis" state={stages.mut} delayIdx={2} />
            <StageRow label="Expression Analysis" state={stages.exp} delayIdx={3} />
            <StageRow label="Integration Orchestrator" state={stages.int} delayIdx={4} />
            <StageRow label="Pathway Enrichment" state={stages.path} delayIdx={5} />
            <StageRow label="Clinical Biomarkers" state={stages.bio} delayIdx={6} />
            <StageRow label="Llama 3.2 Synthesis" state={stages.llm} delayIdx={7} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="panel log-container" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {!isDone && <div className="log-scanner" />}
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
            <div className="panel fade-up" style={{ borderLeft: `4px solid ${c.blue}`, background: `${c.blue}11`, animation: 'pulseGlow 2s infinite' }}>
              <div className="panel-body" style={{ textAlign: 'center', padding: '24px 16px' }}>
                <div style={{ fontWeight: 700, color: c.blue, fontSize: 18, marginBottom: 12, animation: 'popIn 0.5s ease-out both' }}>✓ ANALYSIS COMPLETE</div>
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

app = re.sub(r'/\* ================= LIVE EXECUTION ================= \*/.*?function LiveExecutionPage.*?return \(\n    <div className="page fade-up" style={{ display: \'flex\', flexDirection: \'column\' }}>.*?    </div>\n  \);\n}', live_execution_page, app, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(app)

print("Script execution complete")
