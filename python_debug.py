import sys
import traceback
import hwpx_engine

with open('python_debug.log', 'w', encoding='utf-8') as f:
    f.write("Starting...\n")
    try:
        converter = hwpx_engine.HWPXConverter()
        sample_md = "# 안녕하세요\n\n이것은 **굵은 텍스트**와 *기울임* 텍스트가 있는 단락입니다."
        converter.create_hwpx(sample_md, "test_output2.hwpx")
        f.write("Done!\n")
    except Exception as e:
        f.write("Error:\n")
        f.write(traceback.format_exc())
