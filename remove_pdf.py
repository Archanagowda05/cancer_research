import re

with open(r'frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

# Remove the PDF button
app = app.replace('              <button className="btn btn-primary pdf-btn" onClick={() => window.print()}>Export PDF Report</button>', '')

with open(r'frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(app)

with open(r'frontend\src\App.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Remove the @media print block
css = re.sub(r'/\* ================= PRINT CSS \(PRESERVED\) ================= \*/\s*@media print\s*\{.*?\}', '', css, flags=re.DOTALL)

with open(r'frontend\src\App.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Removed PDF button and CSS')
