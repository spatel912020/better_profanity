from itertools import product
from typing import List, Set

from .utils import (ALLOWED_CHARACTERS, get_complete_path_of_file,
                    get_next_words, get_start_index_of_next_word,
                    load_unicode_symbols)

## GLOBAL VARIABLES ##
CENSOR_WORDSET = set()
CHARS_MAPPING = {
    'a': ('a', '@', '*', '4', '&'),
    'i': ('i', '*', 'l', '!', '1'),
    'o': ('o', '*', '0', '@'),
    'u': ('u', '*', 'v'),
    'v': ('v', '*', 'u'),
    'l': ('l', '1'),
    'e': ('e', '*', '3'),
    's': ('s', '$'),
}

# The max number of additional words forming a swear word. For example:
# - hand job = 1
# - this is a fish = 3
MAX_NUMBER_COMBINATIONS = 1


def load_censor_words(custom_words: List = None):
    """Generate a set of words that need to be censored."""
    global CENSOR_WORDSET
    global MAX_NUMBER_COMBINATIONS

    # Replace the words from `profanity_wordlist.txt` with a custom list
    if custom_words:
        temp_words = custom_words
    else:
        temp_words = read_wordlist()

    all_censor_words = set()
    for word in temp_words:
        num_of_spaces = word.count(" ")
        if num_of_spaces > MAX_NUMBER_COMBINATIONS:
            MAX_NUMBER_COMBINATIONS = num_of_spaces

        all_censor_words.update(set(generate_patterns_from_word(word)))

    # The default wordlist takes ~5MB+ of memory
    CENSOR_WORDSET = all_censor_words


def generate_patterns_from_word(word: str) -> Set[str]:
    """Return all patterns can be generated from the word."""
    combos = [
        (char,) if char not in CHARS_MAPPING else CHARS_MAPPING[char]
        for char in iter(word)
    ]
    return (''.join(pattern) for pattern in product(*combos))


def read_wordlist() -> Set[str]:
    """Return words from file `profanity_wordlist.txt`."""

    wordlist_filename = 'profanity_wordlist.txt'
    wordlist_path = get_complete_path_of_file(wordlist_filename)
    try:
        with open(wordlist_path, encoding='utf-8') as wordlist_file:
            # All words must be in lowercase
            for row in iter(wordlist_file):
                row = row.strip()
                if row != "":
                    yield row
    except FileNotFoundError:
        print('Unable to find profanity_wordlist.txt')
        pass


def get_replacement_for_swear_word(censor_char: str) -> str:
    return censor_char * 4


def contains_profanity(text: str) -> bool:
    """Return True if  the input text has any swear words."""
    return text != censor(text)


def update_next_words_indices(
    text: str, words_indices: List[tuple], start_idx: int
) -> List[tuple]:
    if not words_indices:
        words_indices = get_next_words(text, start_idx + 1, MAX_NUMBER_COMBINATIONS)
    else:
        words_indices.pop(0)
        if words_indices and words_indices[-1][0] != "":
            words_indices += get_next_words(text, words_indices[-1][1], 1)

    return words_indices


def any_next_words_form_swear_word(
    cur_word: str, text: str, words_indices: List[tuple], censor_words: Set[str]
):
    full_word = cur_word.lower()
    for next_word, end_index in iter(words_indices):
        full_word = "%s %s" % (full_word, next_word.lower())
        if full_word in CENSOR_WORDSET:
            return True, end_index
    return False, -1


def hide_swear_words(text: str, censor_char: str) -> str:
    """Replace the swear words with censor characters."""
    censored_text = ""
    cur_word = ""
    skip_index = -1
    skip_cur_char = False
    next_words_indices = []
    start_idx_of_next_word = get_start_index_of_next_word(text, 0)

    # If there are no words in the text, return the raw text without parsing
    if start_idx_of_next_word >= len(text) - 1:
        return text

    # Left strip the text, to avoid inaccurate parsing
    if start_idx_of_next_word > 0:
        censored_text = text[:start_idx_of_next_word]
        text = text.lstrip()

    # Splitting each word in the text to compare with censored words
    for index, char in iter(enumerate(text)):
        if index < skip_index:
            continue
        if char in ALLOWED_CHARACTERS:
            cur_word += char
            continue

        # Iterate the next words combined with the current one
        # to check if it forms a swear word
        next_words_indices = update_next_words_indices(text, next_words_indices, index)
        contains_swear_word, end_index = any_next_words_form_swear_word(
            cur_word, text, next_words_indices, CENSOR_WORDSET
        )
        if contains_swear_word:
            cur_word = get_replacement_for_swear_word(censor_char)
            skip_index = end_index
            char = ""

        # If the current a swear word
        if cur_word.lower() in CENSOR_WORDSET:
            cur_word = get_replacement_for_swear_word(censor_char)

        censored_text += cur_word
        censored_text += char
        cur_word = ""

    # Final check
    if cur_word != "" and skip_index < len(text):
        if cur_word.lower() in CENSOR_WORDSET:
            cur_word = get_replacement_for_swear_word(censor_char)
        censored_text += cur_word
    return censored_text


def censor(text: str, censor_char: str = '*') -> str:
    """Replace the swear words in the text with `censor_char`."""

    if not isinstance(text, str):
        text = str(text)
    if not isinstance(censor_char, str):
        censor_char = str(censor_char)

    if not CENSOR_WORDSET:
        load_censor_words()
    return hide_swear_words(text, censor_char)
