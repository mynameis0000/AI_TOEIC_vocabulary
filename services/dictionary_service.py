from PyDictionary import PyDictionary
import requests
from services.constants import (
    PRIMARY_PARTS_OF_SPEECH,
    BE_VERBS,
    OTHER_PART_OF_SPEECH_WORDS
)

dictionary = PyDictionary()

def get_word_meaning(word):

    try:

        meaning = dictionary.meaning(word)

        if not meaning:
            return "뜻을 찾을 수 없습니다."

        first_part = list(meaning.keys())[0]

        first_meaning = meaning[first_part][0]

        return f"{first_part}: {first_meaning}"

    except Exception as e:

        print(e)

        return "사전 검색 중 오류가 발생했습니다."
    
def get_word_info(word):

    if word.lower() in BE_VERBS:

        return {
            "is_valid": True,
            "parts_of_speech": ["verb"]
        }

    if word.lower() in OTHER_PART_OF_SPEECH_WORDS:

        return {
            "is_valid": True,
            "parts_of_speech": ["other"]
        }

    url = (
        "https://api.dictionaryapi.dev/"
        f"api/v2/entries/en/{word}"
    )

    try:

        response = requests.get(
            url,
            timeout=5
        )

        if response.status_code != 200:

            print(
                f"[사전 API 실패] "
                f"status={response.status_code}"
            )

            return {
                "is_valid": False,
                "parts_of_speech": []
            }

        try:

            entries = response.json()

        except Exception as json_error:

            print(
                f"[JSON 파싱 실패] "
                f"{str(json_error)}"
            )

            return {
                "is_valid": False,
                "parts_of_speech": []
            }

        if not isinstance(entries, list):

            return {
                "is_valid": False,
                "parts_of_speech": []
            }

        part_of_speech_scores = {}

        has_other_part_of_speech = False

        for entry in entries:

            if not isinstance(entry, dict):
                continue

            for meaning in entry.get(
                "meanings",
                []
            ):

                part_of_speech = meaning.get(
                    "partOfSpeech"
                )

                if (
                    part_of_speech
                    in PRIMARY_PARTS_OF_SPEECH
                ):

                    definition_count = len(
                        meaning.get(
                            "definitions",
                            []
                        )
                    ) or 1

                    part_of_speech_scores[
                        part_of_speech
                    ] = (

                        part_of_speech_scores.get(
                            part_of_speech,
                            0
                        )

                        + definition_count
                    )

                elif part_of_speech:

                    definition_count = len(
                        meaning.get(
                            "definitions",
                            []
                        )
                    ) or 1

                    has_other_part_of_speech = True

                    part_of_speech_scores[
                        "other"
                    ] = (

                        part_of_speech_scores.get(
                            "other",
                            0
                        )

                        + definition_count
                    )

        parts_of_speech = []

        if part_of_speech_scores:

            primary_part_of_speech = max(
                part_of_speech_scores,
                key=part_of_speech_scores.get
            )

            parts_of_speech.append(
                primary_part_of_speech
            )

        elif has_other_part_of_speech:

            parts_of_speech.append(
                "other"
            )

        return {
            "is_valid": True,
            "parts_of_speech": parts_of_speech
        }

    except Exception as error:

        print(
            f"[get_word_info 오류] "
            f"{str(error)}"
        )

        return {
            "is_valid": False,
            "parts_of_speech": []
        }
