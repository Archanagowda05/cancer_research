import os
import re

with open(r'frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

# Add new icons
if 'UploadCloud' not in app:
    app = app.replace('FlaskConical', 'FlaskConical, UploadCloud, FileText, UserPlus')

# Add the DataEntryPage component before App component
data_page = """
/* ================= DATA IMPORT ================= */
function DataEntryPage({ t, c }) {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  
  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const newFiles = Array.from(e.dataTransfer.files).map(f => ({ name: f.name, size: (f.size / 1024 / 1024).toFixed(2) + ' MB' }));
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  return (
    <div className="page fade-up">
      <div className="page-head">
        <div className="eyebrow">Data Collection</div>
        <h1 className="page-title">Cohort Import &amp; Metadata</h1>
        <div className="page-sub">Upload custom omics datasets or manually append clinical records</div>
      </div>
      <LocusDivider label="DATA ENTRY" />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 10 }}>
        
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Omics Dataset Upload</span>
            <UploadCloud size={14} color={c.blue} />
          </div>
          <div className="panel-body">
            <div 
              className="drop-zone"
              onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
              style={{
                border: `2px dashed ${dragActive ? c.blue : c.lineStrong}`,
                background: dragActive ? `${c.blue}11` : c.surface2,
                borderRadius: 4, padding: '40px 20px', textAlign: 'center', transition: 'all 0.2s ease', cursor: 'pointer'
              }}
            >
              <UploadCloud size={32} color={dragActive ? c.blue : c.inkFaint} style={{ marginBottom: 12 }} />
              <div style={{ fontFamily: 'IBM Plex Mono', fontSize: 13, fontWeight: 600, color: c.ink, marginBottom: 4 }}>Drag &amp; drop files here</div>
              <div style={{ fontSize: 11, color: c.inkFaint }}>Supports .txt (MAF), .tsv (RSEM), .csv (Clinical)</div>
            </div>

            {files.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: c.inkFaint, marginBottom: 8 }}>Staged Files</div>
                {files.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', border: `1px solid ${c.line}`, borderRadius: 4, marginBottom: 6 }}>
                    <FileText size={14} color={c.inkDim} />
                    <div style={{ flex: 1, fontFamily: 'IBM Plex Mono', fontSize: 12, fontWeight: 600 }}>{f.name}</div>
                    <div style={{ fontSize: 11, color: c.inkFaint }}>{f.size}</div>
                  </div>
                ))}
                <button className="btn btn-primary" style={{ width: '100%', marginTop: 10 }}>Process Custom Cohort</button>
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Manual Patient Entry</span>
            <UserPlus size={14} color={c.green} />
          </div>
          <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="spec-grid">
              <div className="field">
                <span className="field-label">PATIENT ID</span>
                <input type="text" placeholder="e.g. TCGA-A1-A0SB" style={{ width: '100%' }} />
              </div>
              <div className="field">
                <span className="field-label">AGE AT DIAGNOSIS</span>
                <input type="number" placeholder="e.g. 54" style={{ width: '100%' }} />
              </div>
            </div>
            
            <div className="spec-grid">
              <div className="field">
                <span className="field-label">BIOLOGICAL SEX</span>
                <select style={{ width: '100%' }}>
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other / Unknown</option>
                </select>
              </div>
              <div className="field">
                <span className="field-label">TUMOR STAGE</span>
                <select style={{ width: '100%' }}>
                  <option>Stage I</option>
                  <option>Stage II</option>
                  <option>Stage III</option>
                  <option>Stage IV</option>
                </select>
              </div>
            </div>

            <div className="spec-grid">
              <div className="field">
                <span className="field-label">OVERALL SURVIVAL (MONTHS)</span>
                <input type="number" placeholder="e.g. 24.5" style={{ width: '100%' }} />
              </div>
              <div className="field">
                <span className="field-label">SURVIVAL STATUS</span>
                <select style={{ width: '100%' }}>
                  <option>Living</option>
                  <option>Deceased</option>
                </select>
              </div>
            </div>

            <button className="btn btn-primary" style={{ marginTop: 'auto', alignSelf: 'flex-start', background: c.green, color: '#fff' }}>Append to Clinical Dataset</button>
          </div>
        </div>

      </div>
    </div>
  );
}

"""

if 'function DataEntryPage' not in app:
    app = app.replace('/* ================= APP SHELL ================= */', data_page + '/* ================= APP SHELL ================= */')

# Add "data" to tabs
app = re.sub(r"const TABS = \['overview',", "const TABS = ['data', 'overview',", app)

# Add "data" to renderContent switch
if "case 'data':" not in app:
    app = app.replace("case 'overview':", "case 'data': return <DataEntryPage t={t} c={c} />;\n      case 'overview':")

# Default start page to "data" if we want to show it off? Let's leave it as overview but user can click it.
# Actually let's make it the default page since the user wants to focus on it.
app = app.replace("const [page, setPage] = useState('overview');", "const [page, setPage] = useState('data');")


with open(r'frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)

print("Injected DataEntryPage successfully")
