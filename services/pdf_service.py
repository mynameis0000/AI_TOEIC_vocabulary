import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO

def register_korean_font():
    # 1. 폰트 파일 경로 설정 (현재 파일 기준 상위 폴더 -> fonts 폴더 -> 파일)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, '..', 'fonts', 'NanumMyeongjo.ttf')
    
    # 2. 폰트 등록
    if 'KoreanFont' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
    
    # 3. 폰트 패밀리 매핑 (이름 통일)
    pdfmetrics.registerFontFamily(
        'KoreanFont',
        normal='KoreanFont',
        bold='KoreanFont',
        italic='KoreanFont',
        boldItalic='KoreanFont'
    )

def build_pdf(words):
    register_korean_font() # 폰트 등록 및 패밀리 매핑 실행
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    table_data = [["No.", "English", "Korean", "Part of Speech"]]
    for i, w in enumerate(words, start=1):
        table_data.append([
            str(i), 
            w.get("word", ""), 
            w.get("meaning", ""), 
            ", ".join(w.get("partsOfSpeech", []))
        ])
    
    table = Table(table_data, colWidths=[40, 150, 180, 120])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'KoreanFont'), # 별칭 적용
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    
    doc.build([table])
    buffer.seek(0)
    return buffer