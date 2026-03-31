import streamlit as st
import tempfile
import os
from hwpx_engine import HWPXConverter
from pdf_engine import PDFConverter

st.set_page_config(page_title="Markdown to HWPX/PDF Converter", page_icon="📝")

st.title("📝 마크다운 → 한글(HWPX) 변환기")
st.markdown("마크다운 텍스트를 입력하거나 `.md` 파일을 업로드하면 한글 파일(.hwpx)로 변환하여 다운로드할 수 있습니다.")

# MD 파일 업로드
uploaded_file = st.file_uploader("MD 파일 업로드 (선택)", type=["md", "txt", "markdown"])

initial_text = ""
if uploaded_file is not None:
    initial_text = uploaded_file.read().decode("utf-8")
    st.success(f"파일 로드 완료: {uploaded_file.name}")

# 입력 창 (업로드된 파일 내용이 있으면 자동으로 채움)
md_input = st.text_area(
    "마크다운 내용을 입력하세요:",
    value=initial_text,
    height=400,
    placeholder="# 제목\n\n내용을 입력하세요...",
)

if st.button("HWPX 파일로 변환하기"):
    if not md_input.strip():
        st.error("내용을 입력해주세요!")
    else:
        try:
            converter = HWPXConverter()

            with tempfile.NamedTemporaryFile(suffix='.hwpx', delete=False) as tmp:
                tmp_path = tmp.name

            converter.create_hwpx(md_input, tmp_path)

            with open(tmp_path, "rb") as f:
                hwpx_bytes = f.read()
            os.unlink(tmp_path)

            # 다운로드 파일명: 업로드된 파일 이름 기반
            if uploaded_file is not None:
                download_name = os.path.splitext(uploaded_file.name)[0] + ".hwpx"
            else:
                download_name = "converted_document.hwpx"

            st.download_button(
                label="📄 변환된 HWPX 다운로드",
                data=hwpx_bytes,
                file_name=download_name,
                mime="application/octet-stream",
            )
            
            # --- PDF 처리 ---
            pdf_converter = PDFConverter()
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                pdf_tmp_path = tmp_pdf.name
                
            pdf_converter.create_pdf(md_input, pdf_tmp_path)
            
            with open(pdf_tmp_path, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(pdf_tmp_path)
            
            if uploaded_file is not None:
                pdf_download_name = os.path.splitext(uploaded_file.name)[0] + ".pdf"
            else:
                pdf_download_name = "converted_document.pdf"
            
            st.download_button(
                label="📕 변환된 PDF 다운로드",
                data=pdf_bytes,
                file_name=pdf_download_name,
                mime="application/pdf",
            )
            
            st.success("변환이 완료되었습니다! 위 버튼을 눌러 원하는 포맷을 다운로드하세요.")

        except Exception as e:
            st.error(f"변환 중 오류가 발생했습니다: {str(e)}")

st.divider()
st.caption("© 2026 Markdown to HWPX Converter | 만든이: 사곡고 수석교사 최연호")
