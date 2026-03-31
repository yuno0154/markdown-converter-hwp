import zipfile
import html
import re
import os

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')
UNORDERED_LIST_RE = re.compile(r'^(\s*)[*\-+]\s+(.*)')
ORDERED_LIST_RE = re.compile(r'^(\s*)\d+\.\s+(.*)')
CODE_FENCE_RE = re.compile(r'^```')
HR_RE = re.compile(r'^(\*{3,}|-{3,}|_{3,})\s*$')
INLINE_RE = re.compile(r'\*\*(.+?)\*\*|__(.+?)__|`(.+?)`|\*(.+?)\*|_(.+?)_')

HEADING_SIZES = {1: 3200, 2: 2800, 3: 2400, 4: 2200, 5: 2000, 6: 1800}
BODY_SIZE = 1000
CODE_SIZE = 900


def _parse_inline(text):
    runs = []
    last = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > last:
            runs.append((text[last:m.start()], False, False, False))
        if m.group(1) or m.group(2):
            runs.append((m.group(1) or m.group(2), True, False, False))
        elif m.group(3):
            runs.append((m.group(3), False, False, True))
        else:
            runs.append((m.group(4) or m.group(5), False, True, False))
        last = m.end()
    if last < len(text):
        runs.append((text[last:], False, False, False))
    if not runs:
        runs.append((text, False, False, False))
    return runs


def _make_run(text, bold=False, italic=False, code=False):
    sz = CODE_SIZE if code else BODY_SIZE
    safe = html.escape(text)
    attrs = f'sz="{sz}"'
    if bold:
        attrs += ' bold="1"'
    if italic:
        attrs += ' italic="1"'
    return f'<hp:run charPrIDRef="0"><hp:charPr {attrs}/><hp:t>{safe}</hp:t></hp:run>'

def _make_p_tag(runs_xml, indent_level=0):
    indent_xml = f'<hp:pPr><hp:indent left="{indent_level}"/></hp:pPr>' if indent_level > 0 else '<hp:pPr/>'
    return f'<hp:p paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{indent_xml}{runs_xml}</hp:p>'

def _make_heading_paragraph(level, text):
    sz = HEADING_SIZES[level]
    safe = html.escape(text)
    runs_xml = f'<hp:run charPrIDRef="0"><hp:charPr sz="{sz}" bold="1"/><hp:t>{safe}</hp:t></hp:run>'
    return f'  {_make_p_tag(runs_xml)}'

def _make_body_paragraph(text):
    runs_xml = ''.join(_make_run(t, b, i, c) for t, b, i, c in _parse_inline(text))
    return f'  {_make_p_tag(runs_xml)}'

def _make_list_paragraph(text, ordered=False, number=1, indent_level=0):
    prefix = f'{number}. ' if ordered else '• '
    full_text = prefix + text
    runs_xml = ''.join(_make_run(t, b, i, c) for t, b, i, c in _parse_inline(full_text))
    left_indent = (indent_level + 1) * 600
    return f'  {_make_p_tag(runs_xml, left_indent)}'

def _make_code_block_paragraph(text):
    safe = html.escape(text)
    runs_xml = f'<hp:run charPrIDRef="0"><hp:charPr sz="{CODE_SIZE}"/><hp:t>{safe}</hp:t></hp:run>'
    return f'  {_make_p_tag(runs_xml, 600)}'

def _make_hr_paragraph():
    line = '─' * 40
    runs_xml = f'<hp:run charPrIDRef="0"><hp:charPr sz="{BODY_SIZE}"/><hp:t>{line}</hp:t></hp:run>'
    return f'  {_make_p_tag(runs_xml)}'


class HWPXConverter:
    def __init__(self, template_path=None):
        if template_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.template_path = os.path.join(base_dir, "template.hwpx")
        else:
            self.template_path = template_path

    def markdown_to_hwpx_xml(self, md_text):
        """마크다운 텍스트를 한글 XML(section0.xml)로 변환"""
        lines = md_text.split('\n')
        paragraphs = []
        in_code_block = False
        ordered_counters = {}

        for line in lines:
            if CODE_FENCE_RE.match(line):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                paragraphs.append(_make_code_block_paragraph(line))
                continue

            if not line.strip():
                paragraphs.append('  <hp:p paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:pPr/><hp:run charPrIDRef="0"><hp:t></hp:t></hp:run></hp:p>')
                ordered_counters.clear()
                continue

            m = HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                paragraphs.append(_make_heading_paragraph(level, m.group(2)))
                ordered_counters.clear()
                continue

            if HR_RE.match(line):
                paragraphs.append(_make_hr_paragraph())
                continue

            ul_m = UNORDERED_LIST_RE.match(line)
            if ul_m:
                indent = len(ul_m.group(1)) // 2
                paragraphs.append(_make_list_paragraph(ul_m.group(2), ordered=False, indent_level=indent))
                continue

            ol_m = ORDERED_LIST_RE.match(line)
            if ol_m:
                indent = len(ol_m.group(1)) // 2
                counter = ordered_counters.get(indent, 0) + 1
                ordered_counters[indent] = counter
                paragraphs.append(_make_list_paragraph(ol_m.group(2), ordered=True, number=counter, indent_level=indent))
                continue

            paragraphs.append(_make_body_paragraph(line))
            ordered_counters.clear()

        xml_body = '\n'.join(paragraphs)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"\n'
            '        xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"\n'
            '        xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"\n'
            '        xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"\n'
            '        version="1.0">\n'
            f'{xml_body}\n'
            '</hs:sec>'
        )

    def create_hwpx(self, md_text, output_path):
        """template.hwpx를 복사하여 section0.xml만 교체"""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"템플릿 파일({self.template_path})을 찾을 수 없습니다.")

        section0_content = self.markdown_to_hwpx_xml(md_text)

        with zipfile.ZipFile(self.template_path, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    # mimetype은 템플릿의 것을 사용하되, 무압축(ZIP_STORED)으로 저장하는 것이 원칙이나 
                    # 한글 파일 템플릿에서 그대로 복사해도 보통 문제가 없습니다.
                    if item.filename == 'Contents/section0.xml':
                        # 우리가 만든 본문으로 교체
                        zout.writestr('Contents/section0.xml', section0_content)
                    else:
                        # 나머지 파일은 템플릿에서 그대로 복사
                        zout.writestr(item, zin.read(item.filename))



if __name__ == "__main__":
    converter = HWPXConverter()
    sample_md = """# 안녕하세요

이것은 **굵은 텍스트**와 *기울임* 텍스트가 있는 단락입니다.

## 목록 예시

- 항목 1
- 항목 2
  - 중첩 항목

1. 첫 번째
2. 두 번째

## 코드 예시

```python
print("Hello, World!")
```

인라인 `코드`도 지원합니다.

---

마지막 단락입니다."""
    converter.create_hwpx(sample_md, "test_output2.hwpx")
    print("test_output2.hwpx 생성 완료")
