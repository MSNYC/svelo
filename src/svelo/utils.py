import re
import string

PRINTABLE = set(string.printable)
COMMON_WORDS = {
    "the",
    "be",
    "to",
    "of",
    "and",
    "a",
    "in",
    "that",
    "have",
    "i",
    "it",
    "for",
    "not",
    "on",
    "with",
    "he",
    "as",
    "you",
    "do",
    "at",
    "this",
    "but",
    "his",
    "by",
    "from",
    "they",
    "we",
    "say",
    "her",
    "she",
    "or",
    "an",
    "will",
    "my",
    "one",
    "all",
    "would",
    "there",
    "their",
    "what",
    "so",
    "up",
    "out",
    "if",
    "about",
    "who",
    "get",
    "which",
    "go",
    "hello",
    "me",
    "world",
}


def clean_whitespace(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def pad_to_multiple(text: str, block: int, pad_char: str = "=") -> str:
    if block <= 0:
        return text
    missing = (-len(text)) % block
    if missing:
        return text + (pad_char * missing)
    return text


def to_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch in PRINTABLE)
    return printable / len(text)


def hexlike_ratio(text: str) -> float:
    raw = re.sub(r"\s+", "", text)
    if not raw:
        return 0.0
    hex_chars = sum(1 for ch in raw if ch.lower() in "0123456789abcdef")
    return hex_chars / len(raw)


def similarity_ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    min_len = min(len(left), len(right))
    max_len = max(len(left), len(right))
    if min_len == 0 or max_len == 0:
        return 0.0
    matches = sum(1 for i in range(min_len) if left[i] == right[i])
    return (matches / min_len) * (min_len / max_len)


def is_ctf_flag(text: str) -> bool:
    """
    Detect if text matches common CTF flag patterns.

    Common patterns include:
    - picoCTF{...}
    - flag{...}
    - CTF{...}
    - HTB{...}
    - And other variations with curly braces

    Args:
        text: The text to check for flag patterns

    Returns:
        True if the text matches a CTF flag pattern, False otherwise
    """
    if not text:
        return False

    # Strip whitespace for pattern matching
    stripped = text.strip()

    # Check for common CTF flag patterns with curly braces
    # Pattern: word characters followed by {content}
    flag_pattern = r'\w+\{.+\}'

    return bool(re.search(flag_pattern, stripped))


def english_score(text: str) -> float:
    if not text:
        return 0.0
    total = len(text)
    printable = sum(1 for ch in text if ch in PRINTABLE)
    printable_ratio_value = printable / total

    letters = sum(1 for ch in text if ch.isalpha())
    spaces = sum(1 for ch in text if ch.isspace())
    digits = sum(1 for ch in text if ch.isdigit())
    vowels = sum(1 for ch in text.lower() if ch in "aeiou" and ch.isalpha())

    alpha_ratio = letters / total
    space_ratio = spaces / total
    digit_ratio = digits / total
    vowel_ratio = vowels / letters if letters else 0.0

    words = re.findall(r"[A-Za-z]{2,}", text)
    if words:
        hits = sum(1 for word in words if word.lower() in COMMON_WORDS)
        word_score = hits / len(words)
    else:
        word_score = 0.0

    signal = (
        0.45 * alpha_ratio
        + 0.2 * space_ratio
        + 0.2 * vowel_ratio
        + 0.15 * word_score
    )
    score = printable_ratio_value * (0.2 + 0.8 * signal)
    score *= max(0.0, 1.0 - 0.6 * digit_ratio)

    if hexlike_ratio(text) > 0.9 and space_ratio < 0.05:
        score *= 0.3

    return max(0.0, min(1.0, score))
