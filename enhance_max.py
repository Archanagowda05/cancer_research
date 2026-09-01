import os
import re

with open(r'frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

# 1. Add Typewriter Component and Spotlight Effect
hooks_inject = """
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

"""

if 'function Typewriter' not in app:
    app = app.replace('/* ================= OVERVIEW ================= */', hooks_inject + '/* ================= OVERVIEW ================= */')

# Use Typewriter for the finding-text in OverviewPage and MultiOmicsPage
app = app.replace('<div className="finding-text">{int.hypothesis}</div>', '<div className="finding-text"><Typewriter text={int.hypothesis} /></div>')

# 2. Add Spotlight Effect and Command Palette state to App
app_inject = """
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

"""
app = app.replace('  const [showIntro, setShowIntro] = useState(() => sessionStorage.getItem(\'omni-intro-seen\') !== \'1\');', '  const [showIntro, setShowIntro] = useState(() => sessionStorage.getItem(\'omni-intro-seen\') !== \'1\');\n' + app_inject)

# 3. Add Ambient Background Particles to Shell
shell_particles = """
      <div className="ambient-bg">
        <div className="blob b1"></div>
        <div className="blob b2"></div>
        <div className="blob b3"></div>
      </div>
      <div className="shell glass-shell">
"""
app = app.replace('<div className="shell">', shell_particles)

# 4. Command Palette JSX and Chat bouncing dots
cmd_jsx = """
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
"""
app = app.replace('{chatOpen && (', cmd_jsx + '\n      {chatOpen && (')

# Typing indicator in chat
typing_indicator = """
            {chatting && (
              <div className="chat-msg ai typing-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            )}
"""
app = app.replace('{chatting && <div className="chat-msg ai" style={{fontStyle:\'italic\', color:c.inkFaint}}>Thinking...</div>}', typing_indicator)

with open(r'frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)


# CSS Enhancements
css_append = """
/* ================= MAXIMUM ENHANCEMENTS ================= */

/* Ambient Blobs Background */
.ambient-bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; background: var(--paper); }
.blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 14s infinite ease-in-out alternate; }
.blob.b1 { width: 400px; height: 400px; background: var(--c-blue-bg); top: -100px; left: -100px; }
.blob.b2 { width: 300px; height: 300px; background: var(--a-green-bg); bottom: -50px; right: -50px; animation-delay: -5s; }
.blob.b3 { width: 350px; height: 350px; background: var(--t-red-bg); bottom: 40%; left: 30%; animation-delay: -9s; opacity: 0.2; }
@keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(40px, -60px) scale(1.1); } }

/* Glassmorphism Shell */
.glass-shell { background: transparent !important; z-index: 1; }
.masthead { background: rgba(var(--surface-rgb), 0.7) !important; backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
:root[data-theme='light'] { --surface-rgb: 255, 255, 255; }
:root[data-theme='dark'] { --surface-rgb: 18, 25, 23; }

/* Spotlight Effect on Cards */
.panel, .conv-card, .dossier-card { position: relative; }
.panel::after, .conv-card::after, .dossier-card::after {
  content: ''; position: absolute; inset: 0; border-radius: inherit;
  background: radial-gradient(600px circle at var(--mouse-x) var(--mouse-y), rgba(92, 163, 236, 0.08), transparent 40%);
  opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 1;
}
.panel:hover::after, .conv-card:hover::after, .dossier-card:hover::after { opacity: 1; }

/* Typewriter Cursor */
.cursor-blink { animation: blink 1s step-end infinite; font-weight: 700; color: var(--c-blue); }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* Command Palette */
.glass-backdrop { backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
.cmd-palette { background: var(--surface); width: 600px; max-width: 90%; border-radius: 8px; box-shadow: 0 12px 40px rgba(0,0,0,0.3); border: 1px solid var(--line-strong); overflow: hidden; }
.cmd-input-wrap { display: flex; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--line); }
.cmd-input { flex: 1; background: transparent; border: none !important; outline: none !important; font-size: 20px; color: var(--ink); font-family: var(--font-body); }
.cmd-badge { font-size: 10px; background: var(--surface-2); padding: 4px 8px; border-radius: 4px; color: var(--ink-faint); border: 1px solid var(--line); }
.cmd-results { padding: 8px; max-height: 300px; overflow-y: auto; }
.cmd-row { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 6px; cursor: pointer; transition: background 0.15s, transform 0.15s; font-size: 14px; color: var(--ink); }
.cmd-row:hover { background: var(--c-blue-bg); transform: translateX(4px); color: var(--c-blue); }
.cmd-icon { font-size: 16px; opacity: 0.7; }

/* Enhanced Chat Drawer */
.chat-drawer {
  background: rgba(var(--surface-rgb), 0.85) !important;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1) !important;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.4) !important;
  transform-origin: bottom right;
  animation: chatPop 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes chatPop { from { opacity: 0; transform: scale(0.9) translateY(20px); } to { opacity: 1; transform: scale(1) translateY(0); } }

/* Chat Typing Dots */
.typing-dots span { display: inline-block; animation: bounce 1.4s infinite both; font-size: 20px; line-height: 10px; padding: 0 1px; }
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-4px); } }

/* Floating glow on chips */
.gene-chip { position: relative; overflow: hidden; }
.gene-chip::before { content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); transform: skewX(-20deg); transition: 0.5s; }
.gene-chip:hover::before { left: 150%; }

/* Scrollbar styling for glassy panels */
.chat-body::-webkit-scrollbar, .cmd-results::-webkit-scrollbar { width: 6px; }
.chat-body::-webkit-scrollbar-thumb, .cmd-results::-webkit-scrollbar-thumb { background: var(--line-strong); border-radius: 6px; }
"""

with open(r'frontend\src\App.css', 'a', encoding='utf-8') as f:
    f.write(css_append)

print("Maximum enhancements injected successfully")
