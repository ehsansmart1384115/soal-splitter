from flask import Flask, render_template, request, send_file, redirect, url_for
import os, io, zipfile
from werkzeug.utils import secure_filename
from processing import extract_questions, group_by_chapter, generate_outputs

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process():
    file = request.files.get('exam_file')
    if not file or not allowed_file(file.filename):
        return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    qrange = request.form.get('question_range', '').strip()
    if '-' in qrange:
        start, end = map(int, qrange.split('-'))
    else:
        start = end = int(qrange)

    questions = extract_questions(filepath)
    grouped = group_by_chapter(questions, (start, end))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for key, items in grouped.items():
            pdf_bytes, docx_bytes = generate_outputs(key, items)
            zf.writestr(f"{key}.pdf", pdf_bytes)
            zf.writestr(f"{key}.docx", docx_bytes)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='exam_by_chapter.zip',
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
