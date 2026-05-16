import subprocess
import sys

# 1. Force install libraries if Render skipped them
def install_dependencies():
    required_libraries = ["flask", "pdfplumber", "reportlab"]
    for lib in required_libraries:
        try:
            import(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_dependencies()

import os
import re
from flask import Flask, request, send_file, jsonify

app = Flask(name)

# Basic clean HTML layout saved as a single-line string to eliminate hidden syntax formatting bugs
HTML_INTERFACE = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>PDF Re-Formatter Portal</title>'
    '<style>body { font-family: sans-serif; background: #f0f2f5; margin: 40px; } '
    '.container { max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); } '
    'h2 { color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; } '
    '.upload-box { border: 2px dashed #3b82f6; border-radius: 8px; padding: 30px; text-align: center; background: #f8fafc; cursor: pointer; margin: 20px 0; } '
    'button { background: #2563eb; color: white; padding: 12px 24px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; width: 100%; }</style></head>'
    '<body><div class="container"><h2>Exam Booklet PDF Synthesizer</h2><p>Upload your solution PDF to reformat.</p>'
    '<form id="uploadForm"><div class="upload-box" onclick="document.getElementById(\'fileInput\').click()">'
    '<input type="file" id="fileInput" name="file" accept=".pdf" style="display:none;"><span id="fileNameDisplay">Tap here to choose your solution PDF</span>'
    '</div><button type="submit">Rearrange & Download Exam Format</button></form><div id="status" style="margin-top:15px; text-align:center; font-weight:bold;"></div></div>'
    '<script>const fileInput = document.getElementById(\'fileInput\');'
    'fileInput.addEventListener(\'change\', (e) => { if(e.target.files.length > 0) document.getElementById(\'fileNameDisplay\').innerText = "Selected: " + e.target.files[0].name; });'
    'document.getElementById(\'uploadForm\').addEventListener(\'submit\', async (e) => { e.preventDefault(); if(!fileInput.files[0]) return alert("Please select a file.");'
    'const formData = new FormData(); formData.append(\'file\', fileInput.files[0]);'
    'const statusDiv = document.getElementById(\'status\'); statusDiv.innerText = "Processing layout sheets...";'
    'try { const response = await fetch(\'/reformat\', { method: \'POST\', body: formData });'
    'if (response.ok) { statusDiv.innerText = "Success! Downloading..."; const blob = await response.blob();'
    'const downloadUrl = window.URL.createObjectURL(blob); const a = document.createElement(\'a\'); a.href = downloadUrl; a.download = "Formatted_Exam_Booklet.pdf";'
    'document.body.appendChild(a); a.click(); a.remove(); } else { statusDiv.innerText = "Processing error."; } } catch (e) { statusDiv.innerText = "Failed connection."; } });</script></body></html>'
)

def parse_disordered_pdf(file_stream):
    raw_text = ""
    with pdfplumber.open(file_stream) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"

    items = re.split(r'(\n\d+\)\s)', raw_text)
    structured_questions = []
    header_info = items[0].strip() if items else "Exam Paper"
    
    for i in range(1, len(items), 2):
        q_num = items[i].strip()
        q_body = items[i+1].strip() if (i+1) < len(items) else ""
        structured_questions.append({"number": q_num, "content": q_body})
        
    return header_info, structured_questions

def build_sorted_pdf(output_path, header_title, questions):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=14, leading=18, textColor=colors.HexColor('#0d3b66'), alignment=1, spaceAfter=15)
    body_style = ParagraphStyle('B1', parent=styles['BodyText'], fontSize=10, leading=14, textColor=colors.black, spaceAfter=10)

    clean_title = header_title.splitlines()[0] if header_title else "Compiled Exam Booklet"
    story.append(Paragraph(f"<b>{clean_title}</b>", title_style))
    story.append(Spacer(1, 15))
    
    for q in questions:
        full_q_text = f"<b>{q['number']}</b> {q['content']}"
        story.append(Paragraph(full_q_text, body_style))
        story.append(Spacer(1, 8))
        
    doc.build(story)

@app.route('/')
def index():
    return HTML_INTERFACE

@app.route('/reformat', methods=['POST'])
def handle_reformat():
    if 'file' not in request.files:
        return jsonify({"error": "Missing file"}), 400
    uploaded_file = request.files['file']
    try:
        header_title, questions = parse_disordered_pdf(uploaded_file)
        temp_output_path = "generated_output.pdf"
        build_sorted_pdf(temp_output_path, header_title, questions)
        return send_file(temp_output_path, as_attachment=True, download_name="Normalized_Exam.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if name == 'main':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))