import os
import urllib.request
import markdown
from xhtml2pdf import pisa

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
FONT_PATH = os.path.join(BASE_DIR, "NanumGothic.ttf")

def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            print("Downloading Korean font for PDF...")
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        except Exception as e:
            print(f"Error downloading font: {e}")

class PDFConverter:
    def __init__(self):
        download_font()

    def create_pdf(self, md_text, output_path):
        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        font_path = FONT_PATH.replace("\\", "/")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            @font-face {{
                font-family: 'NanumGothic';
                src: url('{font_path}');
            }}
            body {{
                font-family: 'NanumGothic', sans-serif;
                line-height: 1.6;
                padding: 10px;
                color: #333;
                font-size: 14px;
                word-break: keep-all;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 1.2em;
                margin-bottom: 0.5em;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                border: 1px solid #e9ecef;
            }}
            code {{
                font-family: 'Courier New', Courier, monospace;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 1em;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
                text-align: left;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }}
        </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        
        with open(output_path, "wb") as f:
            pisa_status = pisa.CreatePDF(html, dest=f)
            
        if pisa_status.err:
            raise Exception("PDF 생성 중 오류가 발생했습니다.")
