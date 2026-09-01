import os
with open(r'd:\OneDrive\Desktop\major project\cancer research\frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

integration_code = """
// --- MULTI-OMICS INTEGRATION PAGE ---
function genNodes(data, t) {
  const int = data.integration.convergent_genes || {};
  const center = { id: "center", x: 50, y: 50, r: 28, type: "hub", label: "MULTI-OMICS", sublabel: "Convergence", color: t.cyan };
  const nodes = [center];
  const addRing = (items, type, color, rx, ry, spread) => {
    if(!items) return;
    items.forEach((gene, i) => {
      const angle = (i / items.length) * Math.PI * 2 - Math.PI / 2;
      nodes.push({ id: gene, x: rx + Math.cos(angle) * spread, y: ry + Math.sin(angle) * spread * 0.62, r: 16, type, label: gene, color });
    });
  };
  addRing(int.mutated_AND_upregulated || [], "mut_up", t.emerald, 50, 50, 28);
  addRing(int.mutated_AND_downregulated || [], "mut_dn", t.red, 50, 50, 22);
  addRing((int.mutated_only || []).slice(0, 4), "mut", t.cyan, 50, 50, 38);
  addRing((int.deg_only || []).slice(0, 5), "deg", t.violet, 50, 50, 42);
  return nodes;
}

import { useRef } from 'react';

function NetworkCanvas({ data, t, onGeneSelect, selectedGene }) {
  const nodes = useMemo(() => genNodes(data, t), [data, t]);
  const [tick, setTick] = useState(0);
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    let frame;
    const animate = () => { setTick(k => k + 1); frame = requestAnimationFrame(animate); };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, []);

  if(!nodes || nodes.length === 0) return null;
  const center = nodes[0];
  const others = nodes.slice(1);

  const TYPE_COLORS = {
    mut_up: t.emerald, mut_dn: t.red, mut: t.cyan, deg: t.violet, hub: t.cyan
  };

  const nodeJitter = (id, axis) => {
    const seed = id.charCodeAt(0) * 137.5 + id.charCodeAt(id.length - 1) * 41.3;
    const f = axis === "x" ? 0.8 : 1.2;
    return Math.sin(tick * 0.02 + seed) * f;
  };

  return (
    <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", overflow: "visible" }} preserveAspectRatio="xMidYMid meet">
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
          <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="glowStrong">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <radialGradient id="hubGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={t.cyan} stopOpacity="0.3" />
          <stop offset="100%" stopColor={t.cyan} stopOpacity="0" />
        </radialGradient>
      </defs>

      {[22, 34, 44].map((r, i) => (
        <circle key={r} cx="50" cy="50" r={r} fill="none" stroke={t.cyan} strokeWidth="0.15" strokeDasharray={i === 0 ? "2 3" : i === 1 ? "1 4" : "0.5 6"} opacity={0.25} />
      ))}

      {others.map((n, i) => {
        const nx = n.x + nodeJitter(n.id, "x");
        const ny = n.y + nodeJitter(n.id, "y");
        const isSelected = selectedGene && (n.id === selectedGene || center.id === selectedGene);
        const isHovered = hoveredNode === n.id;
        const col = TYPE_COLORS[n.type] || t.cyan;
        const opacity = selectedGene ? (n.id === selectedGene ? 0.9 : 0.1) : (isHovered ? 0.7 : 0.25);
        return (
          <line key={n.id} x1="50" y1="50" x2={nx} y2={ny}
            stroke={col} strokeWidth={isSelected || isHovered ? 0.5 : 0.2}
            opacity={opacity} strokeDasharray="2 2"
          />
        );
      })}

      <circle cx="50" cy="50" r="12" fill="url(#hubGrad)" filter="url(#glowStrong)" />
      <circle cx="50" cy="50" r="10" fill={`${t.bg}CC`} stroke={t.cyan} strokeWidth="0.8" />
      <circle cx="50" cy="50" r="6" fill={`${t.cyan}44`} />
      <circle cx="50" cy="50" r="3" fill={t.cyan} filter="url(#glow)" />
      <text x="50" y="26" textAnchor="middle" fill={t.cyan} fontSize="2.2" fontWeight="700" className="mono" opacity="0.8">MULTI-OMICS</text>
      <text x="50" y="29" textAnchor="middle" fill={t.textDim} fontSize="1.6" opacity="0.7">Convergence Hub</text>

      {others.map((n, i) => {
        const nx = n.x + nodeJitter(n.id, "x");
        const ny = n.y + nodeJitter(n.id, "y");
        const col = TYPE_COLORS[n.type] || t.cyan;
        const isSelected = selectedGene === n.id;
        const isHovered = hoveredNode === n.id;
        const rScale = isSelected ? 1.3 : isHovered ? 1.15 : 1;
        const opacity = selectedGene ? (isSelected ? 1 : 0.3) : (isHovered ? 1 : 0.75);
        const r = (n.r / 10) * rScale;
        return (
          <g key={n.id} transform={`translate(${nx},${ny})`} onClick={() => onGeneSelect(n.id)} style={{ cursor: "pointer" }}
            onMouseEnter={() => setHoveredNode(n.id)} onMouseLeave={() => setHoveredNode(null)}>
            {isSelected && <circle cx="0" cy="0" r={r * 2.5} fill={col} opacity="0.08" />}
            <circle cx="0" cy="0" r={r * 1.8} fill={col} opacity="0.08" />
            <circle cx="0" cy="0" r={r} fill={`${t.bg}CC`} stroke={col} strokeWidth={isSelected ? 0.8 : 0.5} opacity={opacity} filter={isSelected || isHovered ? "url(#glow)" : "none"} style={{ transition: "r 0.2s, stroke-width 0.2s" }} />
            <circle cx="0" cy="0" r={r * 0.45} fill={col} opacity={opacity} />
            <text x="0" y={r + 2.2} textAnchor="middle" fill={isSelected ? col : t.textMid} fontSize="1.8" fontWeight={isSelected ? "700" : "500"} className="mono" opacity={opacity} style={{ pointerEvents: "none" }}>{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

import { Brain } from "lucide-react";

function MultiOmicsPage({ data, cancer, t }) {
  const int = data.integration;
  const conv = int.convergent_genes || {};
  const [sel, setSel] = useState(null);

  const TYPE_INFO = [
    { key: "mutated_AND_upregulated", label: "Mutated + Upregulated", color: t.emerald },
    { key: "mutated_AND_downregulated", label: "Mutated + Downregulated", color: t.red },
    { key: "mutated_only", label: "Mutation Only", color: t.cyan },
    { key: "deg_only", label: "Expression Only", color: t.violet },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", height: "100%", overflow: "hidden" }}>
      <div className="fade-up" style={{ display: "flex", flexDirection: "column", borderRight: `1px solid ${t.border}` }}>
        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${t.border}` }}>
          <div style={{ fontSize: 9, color: t.textDim, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 3 }}>Multi-Omics Integration · {cancer}</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: t.text, letterSpacing: "-0.02em" }}>Molecular Convergence Map</h2>
        </div>
        <div style={{ flex: 1, position: "relative", padding: 10 }}>
          <NetworkCanvas data={data} t={t} onGeneSelect={g => setSel(g === sel ? null : g)} selectedGene={sel} />
        </div>
        <div style={{ borderTop: `1px solid ${t.border}`, padding: "10px 20px", display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 0 }}>
          {[
            { label: "Mut + Up", value: (conv.mutated_AND_upregulated||[]).length, color: t.emerald },
            { label: "Mut + Down", value: (conv.mutated_AND_downregulated||[]).length, color: t.red },
            { label: "Mut Only", value: (conv.mutated_only||[]).length, color: t.cyan },
            { label: "DEG Only", value: (conv.deg_only||[]).length, color: t.violet },
          ].map(({ label, value, color }, i) => (
            <div key={label} style={{ textAlign: "center", borderRight: i < 3 ? `1px solid ${t.border}` : "none", padding: "4px 0" }}>
              <div className="mono" style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
              <div style={{ fontSize: 9, color: t.textDim }}>{label}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="fade-up-1" style={{ overflow: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ padding: 14, background: `${t.violet}10`, border: `1px solid ${t.violet}33`, borderRadius: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <Brain size={12} color={t.violet} />
            <span style={{ fontSize: 10, fontWeight: 700, color: t.violet }}>AI HYPOTHESIS</span>
          </div>
          <p style={{ fontSize: 11, color: t.textMid, lineHeight: 1.7 }}>{int.hypothesis}</p>
        </div>
        <div>
          <div style={{ fontSize: 9, fontWeight: 700, color: t.textDim, letterSpacing: "0.1em", marginBottom: 8 }}>PRIORITY TARGETS</div>
          {(int.priority_targets || []).map((g, i) => (
            <div key={g} onClick={() => setSel(g === sel ? null : g)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", marginBottom: 6, borderRadius: 7, background: sel === g ? `${t.cyan}12` : t.surface, border: `1px solid ${sel === g ? t.borderMid : t.border}`, cursor: "pointer" }}>
              <span className="mono" style={{ fontSize: 9, color: t.textDim, width: 16 }}>0{i + 1}</span>
              <div style={{ flex: 1 }}>
                <span className="mono" style={{ fontSize: 14, fontWeight: 700, color: sel === g ? t.cyan : t.text }}>{g}</span>
                <div style={{ fontSize: 9, color: t.textDim, marginTop: 1 }}>Mutation + Expression · {cancer}</div>
              </div>
              <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 3, background: `${t.amber}18`, color: t.amber, fontWeight: 700 }}>HIGH</span>
            </div>
          ))}
        </div>
        {TYPE_INFO.map(({ key, label, color }) => (
          <div key={key}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <div style={{ fontSize: 10, fontWeight: 600, color }}>{label}</div>
              <div className="mono" style={{ fontSize: 10, color: t.textDim }}>{(conv[key]||[]).length}</div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {(conv[key] || []).map(g => (
                <span key={g} onClick={() => setSel(g === sel ? null : g)} className="mono" style={{ fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 4, background: `${color}12`, border: `1px solid ${color}33`, color: sel === g ? color : t.textMid, cursor: "pointer" }}>{g}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

fallback_code = '''    return (
      <div style={{ padding: 40, textAlign: 'center', color: t.textMid }}>
        <Database size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
        <h2>{page} coming soon</h2>
      </div>
    );'''

app = app.replace(fallback_code, "    if (page === 'integration') return <MultiOmicsPage data={data} cancer={cancer} t={t} />;\n" + fallback_code)

app = app.replace("Activity, Target, User", "Activity, Target, User, Brain")

app = app.replace("export default function App()", integration_code + "\\n\\nexport default function App()")

with open(r'd:\OneDrive\Desktop\major project\cancer research\frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)
print('MultiOmicsPage injected!')
