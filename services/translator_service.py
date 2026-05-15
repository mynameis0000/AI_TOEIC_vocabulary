import requests

from googletrans import Translator

translator = Translator()


def translate_word(word):

    try:

        # 영어 단어 존재 확인
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        response = requests.get(url)

        # 존재하지 않는 단어
        if response.status_code != 200:

            return "❌존재하지 않는 영어 단어입니다."

        # 번역
        result = translator.translate(
            word,
            src='en',
            dest='ko'
        )

        return f"✅ {result.text}"

    except Exception as e:

        print(e)

        return "번역 중 오류가 발생했습니다."