from difflib import SequenceMatcher
from services.constants import (
    COMMON_WORDS,
    WORD_FREQUENCY_RANKS
)


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
