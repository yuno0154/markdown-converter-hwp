from flask import Flask, request, send_file
import io
import os
import tempfile
from hwpx_engine import HWPXConverter

app = Flask(__name__)
converter = HWPXConverter()


@app.route('/')
def index():
    return open('index.html', encoding='utf-8').read()


@app.route('/convert', methods=['POST'])
def convert():
    # MD 파일 업로드 우선, 없으면 textarea 내용 사용
    md_file = request.files.get('md_file')
    if md_file and md_file.filename:
        md_content = md_file.read().decode('utf-8')
    else:
        md_content = request.form.get('markdown', '')

    if not md_content:
        return "No markdown content provided", 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.hwpx', delete=False) as tmp:
            tmp_path = tmp.name

        converter.create_hwpx(md_content, tmp_path)

        with open(tmp_path, 'rb') as f:
            data = io.BytesIO(f.read())
        os.unlink(tmp_path)
        tmp_path = None

        data.seek(0)
        return send_file(data, as_attachment=True, download_name='document.hwpx',
                         mimetype='application/octet-stream')
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return f"Conversion failed: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
