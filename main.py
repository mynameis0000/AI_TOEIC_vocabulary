from flask import Flask, render_template
from flask import request, jsonify
from flask import Response
from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO

from flask import send_file

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.pdfbase import pdfmetrics

from reportlab.pdfbase.cidfonts import UnicodeCIDFont


from services.translator_service import translate_word

app = Flask(__name__)
pdfmetrics.registerFont(
    UnicodeCIDFont("HYSMyeongJo-Medium")
)

PART_OF_SPEECH_LABELS = {
    "noun": "명사",
    "verb": "동사",
    "adjective": "형용사",
    "adverb": "부사",
    "other": "기타"
}


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.get_json() or {}

    word = data.get("word", "").strip()

    if not word:
        return jsonify({
            "success": False,
            "word": "",
            "meaning": "",
            "result": "단어를 입력해주세요."
        }), 400

    result = translate_word(word)

    return jsonify(result)


def build_xlsx(words):

    headers = ["English", "Korean", "Part of speech"]
    rows = [headers]

    for word in words:
        rows.append([
            word.get("word", ""),
            word.get("meaning", ""),
            ", ".join(
                PART_OF_SPEECH_LABELS.get(part_of_speech, part_of_speech)
                for part_of_speech in word.get("partsOfSpeech", [])
            )
        ])

    sheet_rows = []

    for row_index, row in enumerate(rows, start=1):
        cells = []

        for column_index, value in enumerate(row, start=1):
            column_name = chr(64 + column_index)
            cell_ref = f"{column_name}{row_index}"
            escaped_value = escape(str(value))
            cells.append(
                f'<c r="{cell_ref}" t="inlineStr">'
                f"<is><t>{escaped_value}</t></is>"
                "</c>"
            )

        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <cols>
        <col min="1" max="1" width="24" customWidth="1"/>
        <col min="2" max="2" width="30" customWidth="1"/>
        <col min="3" max="3" width="18" customWidth="1"/>
    </cols>
    <sheetData>
        {"".join(sheet_rows)}
    </sheetData>
</worksheet>"""

    output = BytesIO()

    with ZipFile(output, "w", ZIP_DEFLATED) as xlsx:
        xlsx.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
        )
        xlsx.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
        )
        xlsx.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
        <sheet name="Saved Words" sheetId="1" r:id="rId1"/>
    </sheets>
</workbook>"""
        )
        xlsx.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
        )
        xlsx.writestr("xl/worksheets/sheet1.xml", worksheet_xml)

    output.seek(0)

    return output.getvalue()


@app.route("/export/xlsx", methods=["POST"])
def export_xlsx():

    data = request.get_json() or {}
    words = data.get("words", [])
    xlsx_content = build_xlsx(words)

    return Response(
        xlsx_content,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ai-vocabulary.xlsx"
        }
    )

@app.route("/export/pdf", methods=["POST"])
def export_pdf():

    data = request.get_json()

    words = data.get("words", [])

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    korean_style = ParagraphStyle(
        "Korean",
        parent=styles["Normal"],
        fontName="HYSMyeongJo-Medium",
        fontSize=12,
        leading=18
    )

    elements = []

    title = Paragraph(
        "AI Vocabulary",
        korean_style
    )

    subtitle = Paragraph(
        "Saved Words",
        korean_style
    )

    elements.append(title)

    elements.append(subtitle)

    elements.append(Spacer(1, 20))

    table_data = [[
        "No.",
        "English",
        "Korean",
        "Part of Speech"
    ]]

    for index, word in enumerate(words, start=1):

        parts_of_speech = ", ".join(
            word.get("partsOfSpeech", [])
        )

        table_data.append([
            str(index),
            word.get("word", ""),
            word.get("meaning", ""),
            parts_of_speech
        ])

    table = Table(
        table_data,
        colWidths=[40, 150, 180, 120]
    )

    table.setStyle(TableStyle([

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#ede9fe")
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "HYSMyeongJo-Medium"
        ),

        (
            "FONTNAME",
            (0, 1),
            (-1, -1),
            "HYSMyeongJo-Medium"
        ),

        (
            "GRID",
            (0, 0),
            (-1, -1),
            1,
            colors.HexColor("#d1d5db")
        )

    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="ai-vocabulary.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)
