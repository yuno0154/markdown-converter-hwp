import os
import urllib.request
import markdown
from fpdf import FPDF

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
        # 1. 문서 객체 생성
        pdf = FPDF()
        pdf.add_page()
        
        # 2. 한글 폰트 추가 (일반, 굵게, 기울임 모두 기본 폰트로 매핑하여 깨짐 방지)
        pdf.add_font("NanumGothic", "", FONT_PATH)
        pdf.add_font("NanumGothic", "B", FONT_PATH)
        pdf.add_font("NanumGothic", "I", FONT_PATH)
        pdf.set_font("NanumGothic", size=12)
        
        # 3. 마크다운 -> HTML 변환 (fpdf2 호환성을 위해 표, 코드블록 확장)
        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        
        # 4. fpdf2 내장 HTML 파서를 통해 렌더링
        try:
            pdf.write_html(html_content)
        except Exception as e:
            # 복잡한 HTML 파싱 실패시 플레인 텍스트로 보조 출력
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("NanumGothic", "", FONT_PATH)
            pdf.set_font("NanumGothic", size=11)
            fallback_text = "HTML 렌더링을 지원하지 않는 마크다운 문법이 포함되어 텍스트로 대신 출력합니다.\n\n" + md_text
            pdf.multi_cell(0, 10, txt=fallback_text)
            
        # 5. 최종 파일 저장
        pdf.output(output_path)
