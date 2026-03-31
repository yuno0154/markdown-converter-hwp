import streamlit as st
import tempfile
import os
from hwpx_engine import HWPXConverter

st.set_page_config(page_title="Markdown to HWPX Converter", page_icon="📝")

st.title("📝 마크다운 → 한글(HWPX) 변환기")
st.markdown("""
마크다운 텍스트를 입력하고 아래 버튼을 누르면 한글 파일(.hwpx)로 변환하여 다운로드할 수 있습니다.
""")

# 입력 창
md_input = st.text_area("마크다운 내용을 입력하세요:", height=400, placeholder="# 제목\n\n내용을 입력하세요...")

if st.button("HWPX 파일로 변환하기"):
    if not md_input.strip():
        st.error("내용을 입력해주세요!")
    else:
        try:
            converter = HWPXConverter()
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.hwpx', delete=False) as tmp:
                tmp_path = tmp.name
            
            # 변환 실행
            converter.create_hwpx(md_input, tmp_path)
            
            # 파일 읽기 및 다운로드 버튼 생성
            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="📄 변환된 HWPX 다운로드",
                    data=f,
                    file_name="converted_document.hwpx",
                    mime="application/octet-stream"
                )
            
            # 임시 파일 삭제
            os.unlink(tmp_path)
            st.success("변환이 완료되었습니다! 위 버튼을 눌러 다운로드하세요.")
            
        except Exception as e:
            st.error(f"변환 중 오류가 발생했습니다: {str(e)}")

st.divider()
st.caption("© 2026 Markdown to HWPX Converter - Developed for Streamlit")
