import os
from difflib import SequenceMatcher
import json
import requests
import google.generativeai as genai
from googletrans import Translator
from dotenv import load_dotenv

translator = Translator()

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

SUPPORTED_PARTS_OF_SPEECH = [
    "noun",
    "verb",
    "adjective",
    "adverb",
    "other"
]

PRIMARY_PARTS_OF_SPEECH = [
    "noun",
    "verb",
    "adjective",
    "adverb"
]

BE_VERBS = {
    "be",
    "am",
    "is",
    "are",
    "was",
    "were",
    "been",
    "being"
}

OTHER_PART_OF_SPEECH_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "because",
    "if",
    "for",
    "from",
    "of",
    "in",
    "on",
    "to",
    "with",
    "under",
    "over",
    "as"
}

COMMON_WORDS = [
    "ask", "as", "ash", "asp", "ass", "also", "after", "again", "age", "air",
    "all", "am", "an", "and", "any", "apple", "are", "area", "around", "art",
    "at", "away", "baby", "back", "bad", "bag", "ball", "banana", "be", "bed",
    "before", "begin", "best", "better", "big", "bird", "black", "blue", "book",
    "boy", "bring", "build", "bus", "but", "buy", "call", "can", "car", "cat",
    "change", "child", "city", "class", "clean", "close", "cold", "come", "cook",
    "country", "cut", "day", "different", "dog", "do", "door", "down", "draw",
    "drink", "ear", "early", "earth", "eat", "end", "enough", "environment",
    "eye", "face", "fall", "family",
    "far", "fast", "father", "feel", "few", "find", "fine", "fire", "fish",
    "food", "for", "free", "friend", "from", "fruit", "game", "get", "girl",
    "give", "go", "good", "great", "green", "group", "grow", "hand", "happy",
    "hard", "have", "he", "head", "hear", "help", "her", "here", "high", "him",
    "his", "home", "hot", "house", "how", "I", "idea", "important", "in", "is",
    "it", "job", "keep", "kind", "know", "large", "last", "late", "learn",
    "leave", "left", "life", "light", "like", "line", "little", "live", "long",
    "look", "love", "lovely", "make", "man", "many", "me", "meet", "money",
    "more", "morning", "mother", "move", "music", "my", "name", "near", "need",
    "new", "next", "night", "no", "not", "now", "number", "of", "off", "old",
    "on", "one", "open", "or", "orange", "other", "out", "over", "page",
    "paper", "part", "people", "place", "play", "point", "put", "quick",
    "quickly", "read", "red", "right", "room", "run", "same", "say", "school",
    "see", "sentence", "set", "she", "short", "show", "side", "sit", "small",
    "so", "some", "sound", "spell", "stand", "start", "stop", "story", "study",
    "take", "talk", "teach", "tell", "that", "the", "their", "them", "then",
    "there", "they", "thing", "think", "this", "time", "to", "tree", "try",
    "under", "up", "use", "very", "walk", "want", "water", "way", "we", "week",
    "well", "what", "when", "where", "white", "who", "why", "will", "with",
    "word", "work", "world", "write", "yellow", "yes", "you", "young", "your"
]

WORD_FREQUENCY_RANKS = {
    word.lower(): index
    for index, word in enumerate(COMMON_WORDS)
}

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


def translate_word_with_gemini(word):

    print(
        f"[Gemini 분석] '{word}' 처리 중"
    )

    prompt = f"""
You are an English vocabulary analyzer.

The input may be:
- a word
- a compound noun
- a phrase
- an English expression

Analyze naturally.

Input:
"{word}"

Rules:
- Respond ONLY JSON
- Translate naturally into Korean
- Choose the most natural part of speech
- Compound nouns are usually noun
- Never say invalid unless meaningless

JSON format:
{{
  "success": true,
  "word": "{word}",
  "meaning": "자연스러운 한국어 뜻",
  "partsOfSpeech": ["noun"],
  "result": "{word} → 뜻"
}}
"""

    try:

        response = model.generate_content(
            prompt,
            request_options={
                "timeout": 30
            }
        )

        clean_text = response.text.strip()

        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]

        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]

        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        clean_text = clean_text.strip()

        result_json = json.loads(
            clean_text
        )

        if "partsOfSpeech" not in result_json:

            result_json["partsOfSpeech"] = [
                "other"
            ]

        result_json["success"] = True

        result_json["result"] = (
            f"{word} → "
            f"{result_json.get('meaning')}"
        )

        return result_json

    except Exception as error:

        print(
            f"[Gemini 실패] {str(error)}"
        )

        return {

            "success": False,

            "word": word,

            "meaning":
                "뜻을 찾을 수 없음",

            "result":
                "AI 서버가 일시적으로 응답하지 않습니다.",

            "suggestions": [],

            "partsOfSpeech": ["other"]
        }

def damerau_levenshtein_distance(first_word, second_word):
    first_length = len(first_word)
    second_length = len(second_word)
    distances = [
        [0] * (second_length + 1)
        for _ in range(first_length + 1)
    ]

    for first_index in range(first_length + 1):
        distances[first_index][0] = first_index

    for second_index in range(second_length + 1):
        distances[0][second_index] = second_index

    for first_index in range(1, first_length + 1):
        for second_index in range(1, second_length + 1):
            substitution_cost = (
                0
                if first_word[first_index - 1] == second_word[second_index - 1]
                else 1
            )

            distances[first_index][second_index] = min(
                distances[first_index - 1][second_index] + 1,
                distances[first_index][second_index - 1] + 1,
                distances[first_index - 1][second_index - 1] + substitution_cost
            )

            if (
                first_index > 1
                and second_index > 1
                and first_word[first_index - 1] == second_word[second_index - 2]
                and first_word[first_index - 2] == second_word[second_index - 1]
            ):
                distances[first_index][second_index] = min(
                    distances[first_index][second_index],
                    distances[first_index - 2][second_index - 2] + 1
                )

    return distances[first_length][second_length]

def is_strict_typo(input_word, candidate):
    distance = damerau_levenshtein_distance(input_word, candidate)
    similarity = SequenceMatcher(None, input_word, candidate).ratio()

    if len(input_word) <= 3:
        return distance <= 1 and similarity >= 0.6

    if len(input_word) <= 7:
        return distance <= 2 and similarity >= 0.68

    return distance <= 2 and similarity >= 0.74

def is_soft_similarity(input_word, candidate):
    distance = damerau_levenshtein_distance(input_word, candidate)
    similarity = SequenceMatcher(None, input_word, candidate).ratio()
    length_gap = abs(len(candidate) - len(input_word))
    has_prefix_match = (
        len(input_word) >= 4
        and candidate.startswith(input_word)
    )

    if len(input_word) <= 3:
        return distance <= 2 or similarity >= 0.45

    if has_prefix_match:
        return length_gap <= 7

    if len(input_word) <= 6:
        return distance <= 3 or similarity >= 0.55

    return distance <= 4 or similarity >= 0.62

def score_spelling_candidate(input_word, candidate):
    distance = damerau_levenshtein_distance(input_word, candidate)
    length_gap = abs(len(candidate) - len(input_word))
    prefix_similarity = 0

    for input_char, candidate_char in zip(input_word, candidate):
        if input_char != candidate_char:
            break

        prefix_similarity += 1

    return (
        -prefix_similarity,
        distance,
        length_gap,
        WORD_FREQUENCY_RANKS.get(candidate, len(COMMON_WORDS))
    )

def suggest_words_by_rule(word, matcher):
    normalized_word = word.lower()
    scored_words = []

    for candidate in COMMON_WORDS:
        normalized_candidate = candidate.lower()

        if normalized_candidate == normalized_word:
            continue

        if not matcher(normalized_word, normalized_candidate):
            continue

        scored_words.append(
            score_spelling_candidate(normalized_word, normalized_candidate)
            + (normalized_candidate,)
        )

    scored_words.sort()

    return clean_suggestions([
        scored_word[-1]
        for scored_word in scored_words
    ])

def suggest_words_by_strict_typo(word):
    return suggest_words_by_rule(word, is_strict_typo)

def suggest_words_by_soft_similarity(word):
    return suggest_words_by_rule(word, is_soft_similarity)

def suggest_expanded_forms(word):
    normalized_word = word.lower()

    if len(normalized_word) < 4:
        return []

    expanded_forms = [
        candidate.lower()
        for candidate in COMMON_WORDS
        if (
            candidate.lower().startswith(normalized_word)
            and len(candidate) - len(normalized_word) >= 3
        )
    ]

    return clean_suggestions(expanded_forms)

def suggest_words_by_spelling(word):
    strict_suggestions = suggest_words_by_strict_typo(word)

    if strict_suggestions:
        return strict_suggestions

    return suggest_words_by_soft_similarity(word)

def suggest_similar_words(word):

    suggestions = (
        suggest_words_by_strict_typo(
            word
        )
    )

    if suggestions:
        return suggestions

    suggestions = (
        suggest_words_by_soft_similarity(
            word
        )
    )

    if suggestions:
        return suggestions

    return []

def clean_suggestions(suggestions):
    cleaned = []

    for suggestion in suggestions:
        word = suggestion.strip().lower().strip("-•0123456789. )(")

        if word.isalpha() and word not in cleaned:
            cleaned.append(word)

    return cleaned[:3]

def suggest_similar_words_fallback(word):
    normalized_word = word.lower()

    ranked_words = sorted(
        COMMON_WORDS,
        key=lambda candidate: (
            abs(len(candidate) - len(normalized_word)),
            -SequenceMatcher(None, normalized_word, candidate.lower()).ratio(),
            COMMON_WORDS.index(candidate)
        )
    )

    return clean_suggestions(ranked_words[:3])

def build_invalid_word_message(suggestions):
    message = "❌ 존재하지 않는 영어 단어입니다."
    return message

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