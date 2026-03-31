import zipfile
import html
import re

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')
UNORDERED_LIST_RE = re.compile(r'^(\s*)[*\-+]\s+(.*)')
ORDERED_LIST_RE = re.compile(r'^(\s*)\d+\.\s+(.*)')
CODE_FENCE_RE = re.compile(r'^```')
HR_RE = re.compile(r'^(\*{3,}|-{3,}|_{3,})\s*$')
INLINE_RE = re.compile(r'\*\*(.+?)\*\*|__(.+?)__|`(.+?)`|\*(.+?)\*|_(.+?)_')

# charShapeId 정의
CHAR_NORMAL = 0       # 본문 일반
CHAR_BOLD = 1         # 굵게
CHAR_ITALIC = 2       # 기울임
CHAR_BOLD_ITALIC = 3  # 굵게+기울임
CHAR_CODE = 4         # 코드
CHAR_H1 = 5           # 제목1 (32pt)
CHAR_H2 = 6           # 제목2 (28pt)
CHAR_H3 = 7           # 제목3 (24pt)
CHAR_H4 = 8           # 제목4 (22pt)
CHAR_H5 = 9           # 제목5 (20pt)
CHAR_H6 = 10          # 제목6 (18pt)

# paraShapeId 및 styleId 정의
STYLE_NORMAL = 0
STYLE_H1 = 1
STYLE_H2 = 2
STYLE_H3 = 3
STYLE_H4 = 4
STYLE_H5 = 5
STYLE_H6 = 6
STYLE_CODE = 7

HEADING_CHAR = {1: CHAR_H1, 2: CHAR_H2, 3: CHAR_H3, 4: CHAR_H4, 5: CHAR_H5, 6: CHAR_H6}
HEADING_STYLE = {1: STYLE_H1, 2: STYLE_H2, 3: STYLE_H3, 4: STYLE_H4, 5: STYLE_H5, 6: STYLE_H6}
HEADING_SIZES = {1: 3200, 2: 2800, 3: 2400, 4: 2200, 5: 2000, 6: 1800}


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


def _char_id(bold, italic, code):
    if code:
        return CHAR_CODE
    if bold and italic:
        return CHAR_BOLD_ITALIC
    if bold:
        return CHAR_BOLD
    if italic:
        return CHAR_ITALIC
    return CHAR_NORMAL


def _make_run(text, bold=False, italic=False, code=False, char_id=None):
    if char_id is None:
        char_id = _char_id(bold, italic, code)
    safe = html.escape(text)
    return f'<hp:run charPrIDRef="{char_id}"><hp:t>{safe}</hp:t></hp:run>'


def _make_para(style_id, runs_xml, indent_left=0):
    if indent_left:
        return (f'<hp:p paraPrIDRef="{style_id}" styleIDRef="{style_id}" '
                f'pageBreak="0" columnBreak="0" merged="0">'
                f'<hp:pPr><hp:indent left="{indent_left}"/></hp:pPr>'
                f'{runs_xml}</hp:p>')
    return (f'<hp:p paraPrIDRef="{style_id}" styleIDRef="{style_id}" '
            f'pageBreak="0" columnBreak="0" merged="0">{runs_xml}</hp:p>')


def _make_heading_para(level, text):
    char_id = HEADING_CHAR[level]
    style_id = HEADING_STYLE[level]
    safe = html.escape(text)
    runs_xml = f'<hp:run charPrIDRef="{char_id}"><hp:t>{safe}</hp:t></hp:run>'
    return _make_para(style_id, runs_xml)


def _make_body_para(text):
    runs_xml = ''.join(
        _make_run(t, b, i, c)
        for t, b, i, c in _parse_inline(text)
    )
    return _make_para(STYLE_NORMAL, runs_xml)


def _make_list_para(text, ordered=False, number=1, indent_level=0):
    prefix = f'{number}. ' if ordered else '• '
    full_text = prefix + text
    runs_xml = ''.join(
        _make_run(t, b, i, c)
        for t, b, i, c in _parse_inline(full_text)
    )
    left_indent = (indent_level + 1) * 600
    return _make_para(STYLE_NORMAL, runs_xml, indent_left=left_indent)


def _make_code_para(text):
    safe = html.escape(text)
    runs_xml = f'<hp:run charPrIDRef="{CHAR_CODE}"><hp:t>{safe}</hp:t></hp:run>'
    return _make_para(STYLE_CODE, runs_xml, indent_left=600)


def _make_hr_para():
    line = '─' * 40
    safe = html.escape(line)
    runs_xml = f'<hp:run charPrIDRef="{CHAR_NORMAL}"><hp:t>{safe}</hp:t></hp:run>'
    return _make_para(STYLE_NORMAL, runs_xml)


def _make_empty_para():
    return (f'<hp:p paraPrIDRef="{STYLE_NORMAL}" styleIDRef="{STYLE_NORMAL}" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{CHAR_NORMAL}"><hp:t/></hp:run></hp:p>')


class HWPXConverter:

    def markdown_to_section_xml(self, md_text):
        lines = md_text.split('\n')
        paragraphs = []
        in_code_block = False
        ordered_counters = {}

        for line in lines:
            if CODE_FENCE_RE.match(line):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                paragraphs.append(_make_code_para(line))
                continue

            if not line.strip():
                paragraphs.append(_make_empty_para())
                ordered_counters.clear()
                continue

            m = HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                paragraphs.append(_make_heading_para(level, m.group(2)))
                ordered_counters.clear()
                continue

            if HR_RE.match(line):
                paragraphs.append(_make_hr_para())
                continue

            ul_m = UNORDERED_LIST_RE.match(line)
            if ul_m:
                indent = len(ul_m.group(1)) // 2
                paragraphs.append(_make_list_para(ul_m.group(2), ordered=False, indent_level=indent))
                continue

            ol_m = ORDERED_LIST_RE.match(line)
            if ol_m:
                indent = len(ol_m.group(1)) // 2
                counter = ordered_counters.get(indent, 0) + 1
                ordered_counters[indent] = counter
                paragraphs.append(_make_list_para(ol_m.group(2), ordered=True, number=counter, indent_level=indent))
                continue

            paragraphs.append(_make_body_para(line))
            ordered_counters.clear()

        body = '\n'.join(paragraphs)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"\n'
            '        xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"\n'
            '        version="1.0">\n'
            f'{body}\n'
            '</hs:sec>'
        )

    def create_hwpx(self, md_text, output_path):
        section_xml = self.markdown_to_section_xml(md_text)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            # mimetype은 반드시 첫 번째, 압축 없이 저장
            z.writestr(
                zipfile.ZipInfo('mimetype'),
                'application/hwp+zip',
                compress_type=zipfile.ZIP_STORED
            )
            z.writestr('META-INF/container.xml', self._get_container_xml())
            z.writestr('[Content_Types].xml', self._get_content_types_xml())
            z.writestr('_rels/.rels', self._get_rels_xml())
            z.writestr('Contents/content.hpf', self._get_content_hpf())
            z.writestr('Contents/header.xml', self._get_header_xml())
            z.writestr('version.xml', self._get_version_xml())
            z.writestr('Contents/section0.xml', section_xml)

    # ──────────────────────────────────────────────
    # 파일 내용 생성 메서드
    # ──────────────────────────────────────────────

    def _get_container_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<container version="1.0"\n'
            '  xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="Contents/content.hpf"\n'
            '              media-type="application/hwpml-package+xml"/>\n'
            '  </rootfiles>\n'
            '</container>'
        )

    def _get_content_types_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="hpf" ContentType="application/hwpml-package+xml"/>\n'
            '  <Override PartName="/version.xml" ContentType="application/vnd.hancom.hwpml-version+xml"/>\n'
            '  <Override PartName="/Contents/header.xml" ContentType="application/vnd.hancom.hwpml-header+xml"/>\n'
            '  <Override PartName="/Contents/section0.xml" ContentType="application/vnd.hancom.hwpml-section+xml"/>\n'
            '</Types>'
        )

    def _get_rels_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://www.hancom.co.kr/hwpml/2011/relation/contents" Target="Contents/content.hpf"/>\n'
            '</Relationships>'
        )

    def _get_version_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<hc:version xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
            'targetApplication="Hancom Office Hwp 2018" major="10" minor="0" micro="0" buildNumber="0" os="Windows"/>'
        )

    def _get_content_hpf(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<hpf:package xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" version="1.0">\n'
            '  <hpf:metadata>\n'
            '    <hpf:title>Converted Document</hpf:title>\n'
            '  </hpf:metadata>\n'
            '  <hpf:manifest>\n'
            '    <hpf:item id="header" href="header.xml"\n'
            '              media-type="application/vnd.hancom.hwpml-header+xml"/>\n'
            '    <hpf:item id="section0" href="section0.xml"\n'
            '              media-type="application/vnd.hancom.hwpml-section+xml"/>\n'
            '  </hpf:manifest>\n'
            '  <hpf:spine>\n'
            '    <hpf:itemref idref="section0"/>\n'
            '  </hpf:spine>\n'
            '</hpf:package>'
        )

    def _get_header_xml(self):
        # 폰트 정의
        fonts = (
            '<hh:fontFace id="0" lang="HANGUL" name="함초롬바탕" type="TTF"/>\n'
            '    <hh:fontFace id="1" lang="LATIN"  name="함초롬바탕" type="TTF"/>\n'
            '    <hh:fontFace id="2" lang="HANJA"  name="함초롬바탕" type="TTF"/>\n'
            '    <hh:fontFace id="3" lang="JAPANESE" name="함초롬바탕" type="TTF"/>\n'
            '    <hh:fontFace id="4" lang="OTHER"  name="함초롬바탕" type="TTF"/>\n'
            '    <hh:fontFace id="5" lang="SYMBOL" name="Symbol" type="TTF"/>\n'
            '    <hh:fontFace id="6" lang="LATIN"  name="Courier New" type="TTF"/>'
        )

        def char_shape(cid, height, bold=0, italic=0, latin_font=1):
            return (
                f'<hh:charShape id="{cid}" height="{height}" textColor="0" shadeColor="16777215" '
                f'bold="{bold}" italic="{italic}" underline="0" strikeout="0" outline="0" '
                f'emboss="0" engrave="0" superscript="0" subscript="0" shadowType="0" '
                f'fontIdHangul="0" fontIdLatin="{latin_font}" fontIdHanja="2" fontIdJapanese="3" '
                f'fontIdOther="4" fontIdSymbol="5" fontIdUser="0" '
                f'ratioHangul="100" ratioLatin="100" ratioHanja="100" ratioJapanese="100" '
                f'ratioOther="100" ratioSymbol="100" ratioUser="100" '
                f'spacingHangul="0" spacingLatin="0" spacingHanja="0" spacingJapanese="0" '
                f'spacingOther="0" spacingSymbol="0" spacingUser="0" '
                f'kerning="0" baselineHangul="0" baselineLatin="0" baselineHanja="0" '
                f'baselineJapanese="0" baselineOther="0" baselineSymbol="0" baselineUser="0" '
                f'shadowX="0" shadowY="0"/>'
            )

        char_shapes = '\n    '.join([
            char_shape(CHAR_NORMAL,      1000, bold=0, italic=0),
            char_shape(CHAR_BOLD,        1000, bold=1, italic=0),
            char_shape(CHAR_ITALIC,      1000, bold=0, italic=1),
            char_shape(CHAR_BOLD_ITALIC, 1000, bold=1, italic=1),
            char_shape(CHAR_CODE,         900, bold=0, italic=0, latin_font=6),
            char_shape(CHAR_H1, HEADING_SIZES[1], bold=1),
            char_shape(CHAR_H2, HEADING_SIZES[2], bold=1),
            char_shape(CHAR_H3, HEADING_SIZES[3], bold=1),
            char_shape(CHAR_H4, HEADING_SIZES[4], bold=1),
            char_shape(CHAR_H5, HEADING_SIZES[5], bold=1),
            char_shape(CHAR_H6, HEADING_SIZES[6], bold=1),
        ])

        def para_shape(pid, align='JUSTIFY', line_spacing=160, space_before=0, space_after=0):
            return (
                f'<hh:paraShape id="{pid}" align="{align}" '
                f'lineSpacingType="PERCENT" lineSpacing="{line_spacing}" '
                f'spaceBefore="{space_before}" spaceAfter="{space_after}" '
                f'leftMargin="0" rightMargin="0" indent="0" '
                f'tabDistance="4000" tabDistanceSync="1" '
                f'suppressEmptyLine="0"/>'
            )

        para_shapes = '\n    '.join([
            para_shape(STYLE_NORMAL, align='JUSTIFY', line_spacing=160),
            para_shape(STYLE_H1, align='LEFT', line_spacing=160, space_before=500, space_after=300),
            para_shape(STYLE_H2, align='LEFT', line_spacing=160, space_before=400, space_after=200),
            para_shape(STYLE_H3, align='LEFT', line_spacing=160, space_before=300, space_after=150),
            para_shape(STYLE_H4, align='LEFT', line_spacing=160, space_before=200, space_after=100),
            para_shape(STYLE_H5, align='LEFT', line_spacing=160, space_before=200, space_after=100),
            para_shape(STYLE_H6, align='LEFT', line_spacing=160, space_before=200, space_after=100),
            para_shape(STYLE_CODE, align='LEFT', line_spacing=130),
        ])

        def style(sid, name, eng_name, style_type='PARA', char_shape_id=0, para_shape_id=0, next_style=0):
            return (
                f'<hh:style id="{sid}" type="{style_type}" name="{name}" engName="{eng_name}" '
                f'paraPrIDRef="{para_shape_id}" charPrIDRef="{char_shape_id}" '
                f'nextStyleIDRef="{next_style}" langId="1042" lockForm="0"/>'
            )

        styles = '\n    '.join([
            style(STYLE_NORMAL, '바탕글', 'Normal', char_shape_id=CHAR_NORMAL, para_shape_id=STYLE_NORMAL, next_style=STYLE_NORMAL),
            style(STYLE_H1, '제목 1', 'Heading 1', char_shape_id=CHAR_H1, para_shape_id=STYLE_H1, next_style=STYLE_NORMAL),
            style(STYLE_H2, '제목 2', 'Heading 2', char_shape_id=CHAR_H2, para_shape_id=STYLE_H2, next_style=STYLE_NORMAL),
            style(STYLE_H3, '제목 3', 'Heading 3', char_shape_id=CHAR_H3, para_shape_id=STYLE_H3, next_style=STYLE_NORMAL),
            style(STYLE_H4, '제목 4', 'Heading 4', char_shape_id=CHAR_H4, para_shape_id=STYLE_H4, next_style=STYLE_NORMAL),
            style(STYLE_H5, '제목 5', 'Heading 5', char_shape_id=CHAR_H5, para_shape_id=STYLE_H5, next_style=STYLE_NORMAL),
            style(STYLE_H6, '제목 6', 'Heading 6', char_shape_id=CHAR_H6, para_shape_id=STYLE_H6, next_style=STYLE_NORMAL),
            style(STYLE_CODE, '코드', 'Code', char_shape_id=CHAR_CODE, para_shape_id=STYLE_CODE, next_style=STYLE_CODE),
        ])

        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" version="1.0">\n'
            '  <hh:beginNum para="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>\n'
            '  <hh:refList>\n'
            '    <hh:fontFaceList>\n'
            f'    {fonts}\n'
            '    </hh:fontFaceList>\n'
            '    <hh:charShapeList>\n'
            f'    {char_shapes}\n'
            '    </hh:charShapeList>\n'
            '    <hh:paraShapeList>\n'
            f'    {para_shapes}\n'
            '    </hh:paraShapeList>\n'
            '    <hh:styleList>\n'
            f'    {styles}\n'
            '    </hh:styleList>\n'
            '    <hh:trackChangeConfig protect="0"/>\n'
            '  </hh:refList>\n'
            '  <hh:compatibleDocument targetProgram="HWP201X">\n'
            '    <hh:layoutCompatibility/>\n'
            '  </hh:compatibleDocument>\n'
            '  <hh:docOption/>\n'
            '</hh:head>'
        )


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
