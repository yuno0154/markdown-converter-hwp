import os
import urllib.request
import markdown
from xhtml2pdf import pisa

def test_pdf():
    md = "# 테스트\n\n이것은 **한국어** 텍스트와 *기울임* 텍스트입니다."
    html_content = markdown.markdown(md)
    
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        print("Downloading font...")
        urllib.request.urlretrieve(font_url, font_path)
    
    html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{os.path.abspath(font_path).replace("\\", "/")}');
        }}
        body {{
            font-family: 'NanumGothic';
        }}
    </style>
    </head>
    <body>{html_content}</body>
    </html>
    """
    with open("test.pdf", "wb") as f:
        pisa.CreatePDF(html, dest=f)

test_pdf()
print("test.pdf created!")
