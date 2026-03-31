import zipfile
import html
import re

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
    """인라인 마크다운(굵게, 기울임, 코드)을 파싱하여 (text, bold, italic, code) 튜플 리스트 반환"""
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
    return f'<hp:run><hp:charPr {attrs}/><hp:t>{safe}</hp:t></hp:run>'


def _make_heading_paragraph(level, text):
    sz = HEADING_SIZES[level]
    safe = html.escape(text)
    return (
        f'  <hp:p>'
        f'<hp:pPr><hp:pStyle styleId="Heading{level}"/></hp:pPr>'
        f'<hp:run><hp:charPr sz="{sz}" bold="1"/><hp:t>{safe}</hp:t></hp:run>'
        f'</hp:p>'
    )


def _make_body_paragraph(text):
    runs_xml = ''.join(_make_run(t, b, i, c) for t, b, i, c in _parse_inline(text))
    return f'  <hp:p>{runs_xml}</hp:p>'


def _make_list_paragraph(text, ordered=False, number=1, indent_level=0):
    prefix = f'{number}. ' if ordered else '• '
    full_text = prefix + text
    runs_xml = ''.join(_make_run(t, b, i, c) for t, b, i, c in _parse_inline(full_text))
    left_indent = (indent_level + 1) * 600
    return f'  <hp:p><hp:pPr><hp:indent left="{left_indent}"/></hp:pPr>{runs_xml}</hp:p>'


def _make_code_block_paragraph(text):
    safe = html.escape(text)
    return f'  <hp:p><hp:run><hp:charPr sz="{CODE_SIZE}"/><hp:t>{safe}</hp:t></hp:run></hp:p>'


def _make_hr_paragraph():
    line = '─' * 40
    return f'  <hp:p><hp:run><hp:charPr sz="{BODY_SIZE}"/><hp:t>{line}</hp:t></hp:run></hp:p>'


class HWPXConverter:
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
                paragraphs.append('  <hp:p></hp:p>')
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
            '<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="0">\n'
            f'{xml_body}\n'
            '</hp:section>'
        )

    def create_hwpx(self, md_text, output_path):
        """HWPX 파일(ZIP) 패키징"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('mimetype', 'application/hwp+zip', compress_type=zipfile.ZIP_STORED)
            section0_content = self.markdown_to_hwpx_xml(md_text)
            z.writestr('Contents/section0.xml', section0_content)
            z.writestr('[Content_Types].xml', self._get_content_types_xml())
            z.writestr('_rels/.rels', self._get_rels_xml())
            z.writestr('Contents/content.hpf', self._get_content_hpf())

    def _get_content_types_xml(self):
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                '  <Default Extension="xml" ContentType="application/xml"/>\n'
                '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                '  <Override PartName="/Contents/section0.xml" ContentType="application/vnd.hancom.hwpml-paragraph+xml"/>\n'
                '</Types>')

    def _get_rels_xml(self):
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '  <Relationship Id="rId1" Type="http://www.hancom.co.kr/hwpml/2011/relation/contents" Target="Contents/content.hpf"/>\n'
                '</Relationships>')

    def _get_content_hpf(self):
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">\n'
                '  <metadata>\n    <title>Converted Markdown</title>\n  </metadata>\n'
                '  <manifest>\n    <item id="section0" href="section0.xml" media-type="application/vnd.hancom.hwpml-paragraph+xml"/>\n  </manifest>\n'
                '  <spine>\n    <itemref idref="section0"/>\n  </spine>\n</package>')


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
    converter.create_hwpx(sample_md, "test_output.hwpx")
    print("test_output.hwpx 생성 완료")
