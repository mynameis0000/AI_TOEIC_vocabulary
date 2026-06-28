import pandas as pd
from io import BytesIO

def build_xlsx(words):

    processed_words = []
    for w in words:
        pos_list = w.get("partsOfSpeech", [])
        pos_string = ", ".join(pos_list) if isinstance(pos_list, list) else str(pos_list)
        processed_words.append({
            "Word": w.get("word", ""),
            "Meaning": w.get("meaning", ""),
            "Part of Speech": pos_string
        })
    
    df = pd.DataFrame(processed_words)
    
    # 엑셀 저장
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    # [핵심 수정] .getvalue()를 지우고 버퍼의 처음 위치로 이동만 시킵니다.
    output.seek(0)
    return output  # 이제 엑셀 파일 객체(버퍼) 자체가 반환됩니다!