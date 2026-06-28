from googletrans import Translator

from .dictionary_service import get_word_info
from .suggestion_service import (
    suggest_similar_words,
    suggest_similar_words_fallback,
    suggest_expanded_forms,
    build_invalid_word_message
)
from .gemini_service import translate_word_with_gemini

translator = Translator()

def translate_word(word):

    try:

        normalized_word = (
            word.strip().lower()
        )

        if not normalized_word:

            return {

                "success": False,

                "word": "",

                "meaning": "",

                "result":
                    "입력된 단어가 없습니다.",

                "suggestions": [],

                "partsOfSpeech":
                    []
            }

        # 복합 표현은 Gemini 사용
        if " " in normalized_word:

            print(
                f"[복합 표현 감지] "
                f"{normalized_word}"
            )

            return translate_word_with_gemini(
                normalized_word
            )

        # 일반 단어 검사
        word_info = get_word_info(
            normalized_word
        )

        # 존재하지 않는 단어
        if not word_info["is_valid"]:

            try:

                suggestions = (
                    suggest_similar_words(
                        normalized_word
                    )
                )

            except Exception as error:

                print(error)

                suggestions = (
                    suggest_similar_words_fallback(
                        normalized_word
                    )
                )

            return {

                "success": False,

                "word":
                    normalized_word,

                "meaning": "",

                "result":
                    build_invalid_word_message(
                        suggestions
                    ),

                "suggestions":
                    suggestions,

                "partsOfSpeech":
                    []
            }

        # 한국어 번역
        translated = translator.translate(
            normalized_word,
            src="en",
            dest="ko"
        )

        korean_meaning = (
            translated.text
        )

        return {

            "success": True,

            "word":
                normalized_word,

            "meaning":
                korean_meaning,

            "result":
                f"{normalized_word} "
                f"→ {korean_meaning}",

            "suggestions":
                suggest_expanded_forms(
                    normalized_word
                ),

            "partsOfSpeech":
                word_info[
                    "parts_of_speech"
                ]
        }

    except Exception as error:

        print(error)

        return {

            "success": False,

            "word":
                word,

            "meaning": "",

            "result":
                "번역 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",

            "suggestions": [],

            "partsOfSpeech":
                []
        }
