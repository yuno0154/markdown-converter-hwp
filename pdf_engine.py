import markdown
import pdfkit

class PDFConverter:
    def create_pdf(self, md_text, output_path):
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        
        # HTML 템플릿과 CSS 감싸기
        # Streamlit 에서는 fonts-nanum 우분투 패키지를 설치하므로 시스템 폰트로 적용됩니다.
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
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
        
        # wkhtmltopdf 옵션설정 (여백 및 한글 인코딩)
        options = {
            'encoding': 'UTF-8',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'quiet': ''
        }
        
        # PDF 파일 생성
        try:
            pdfkit.from_string(html, output_path, options=options)
        except Exception as e:
            raise Exception("PDF 생성 중 오류가 발생했습니다. (환경 설정 문제일 수 있습니다.) 상세:" + str(e))
