import base64
import binascii
import codecs
import gzip
import zlib
from dataclasses import dataclass
from typing import Callable, List, Optional
from urllib.parse import quote_from_bytes, unquote_to_bytes

from .utils import clean_whitespace, pad_to_multiple


@dataclass(frozen=True)
class DecodeResult:
    name: str
    output: bytes
    note: str = ""


@dataclass(frozen=True)
class Decoder:
    name: str
    description: str
    func: Callable[[str, bytes], List[DecodeResult]]


@dataclass(frozen=True)
class Encoder:
    name: str
    description: str
    func: Optional[Callable[[str], str]] = None


_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_MORSE_TABLE = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    ".-.-.-": ".",
    "--..--": ",",
    "..--..": "?",
    "-.-.--": "!",
    "-..-.": "/",
    "-....-": "-",
    ".----.": "'",
    "-.--.": "(",
    "-.--.-": ")",
}
_BACON_26 = {}
_BACON_24 = {}
_POLYBIUS = {}
_MORSE_REVERSE = {}
_BACON_24_REVERSE = {}
_BACON_26_REVERSE = {}
_POLYBIUS_REVERSE = {}


def _init_bacon_maps() -> None:
    letters_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    letters_24 = "ABCDEFGHIKLMNOPQRSTUWXYZ"
    for idx, ch in enumerate(letters_26):
        bits = format(idx, "05b")
        _BACON_26["".join("A" if bit == "0" else "B" for bit in bits)] = ch
    for idx, ch in enumerate(letters_24):
        bits = format(idx, "05b")
        _BACON_24["".join("A" if bit == "0" else "B" for bit in bits)] = ch
    for key, value in _BACON_24.items():
        _BACON_24_REVERSE[value] = key
    for key, value in _BACON_26.items():
        _BACON_26_REVERSE[value] = key


_init_bacon_maps()


def _init_polybius_map() -> None:
    letters = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    idx = 0
    for row in range(1, 6):
        for col in range(1, 6):
            _POLYBIUS[f"{row}{col}"] = letters[idx]
            idx += 1
    for key, value in _POLYBIUS.items():
        _POLYBIUS_REVERSE[value] = key


_init_polybius_map()
_MORSE_REVERSE.update({value: key for key, value in _MORSE_TABLE.items()})


def _decode_base58(text: str) -> bytes:
    if not text:
        raise ValueError("empty base58 input")
    num = 0
    for ch in text:
        idx = _B58_ALPHABET.find(ch)
        if idx < 0:
            raise ValueError("invalid base58 char")
        num = num * 58 + idx
    if num == 0:
        payload = b""
    else:
        payload = num.to_bytes((num.bit_length() + 7) // 8, "big")
    leading = len(text) - len(text.lstrip("1"))
    return (b"\x00" * leading) + payload


def _encode_base58(data: bytes) -> str:
    if not data:
        return ""
    num = int.from_bytes(data, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = _B58_ALPHABET[rem] + encoded
    leading = len(data) - len(data.lstrip(b"\x00"))
    return ("1" * leading) + encoded


def _try_hex(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if raw.lower().startswith("0x"):
        raw = raw[2:]
    if not raw or len(raw) % 2 != 0:
        return []
    try:
        out = binascii.unhexlify(raw)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("hex", out)]


def encode_hex(text: str) -> str:
    return text.encode("utf-8").hex()


def _try_base64(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if not raw:
        return []
    raw = pad_to_multiple(raw, 4, "=")
    try:
        out = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("base64", out)]


def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _try_base64url(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if not raw:
        return []
    raw = pad_to_multiple(raw, 4, "=")
    try:
        out = base64.urlsafe_b64decode(raw)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("base64url", out)]


def encode_base64url(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def _try_base32(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if not raw:
        return []
    raw = pad_to_multiple(raw, 8, "=")
    try:
        out = base64.b32decode(raw, casefold=True)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("base32", out)]


def encode_base32(text: str) -> str:
    return base64.b32encode(text.encode("utf-8")).decode("ascii")


def _try_base85(text: str, _data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    if not raw:
        return []
    try:
        out = base64.b85decode(raw)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("base85", out)]


def encode_base85(text: str) -> str:
    return base64.b85encode(text.encode("utf-8")).decode("ascii")


def _try_ascii85(text: str, _data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    if not raw:
        return []
    try:
        out = base64.a85decode(raw)
    except (binascii.Error, ValueError):
        return []
    return [DecodeResult("ascii85", out)]


def encode_ascii85(text: str) -> str:
    return base64.a85encode(text.encode("utf-8")).decode("ascii")


def _try_base58(text: str, _data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    if not raw:
        return []
    try:
        out = _decode_base58(raw)
    except ValueError:
        return []
    return [DecodeResult("base58", out)]


def encode_base58(text: str) -> str:
    return _encode_base58(text.encode("utf-8"))


def _try_url(text: str, data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    if not raw:
        return []
    out = unquote_to_bytes(raw)
    if out == data:
        return []
    return [DecodeResult("url", out)]


def encode_url(text: str) -> str:
    return quote_from_bytes(text.encode("utf-8"))


def _try_rot13(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    out_text = codecs.decode(text, "rot_13")
    if out_text == text:
        return []
    return [DecodeResult("rot13", out_text.encode("utf-8"))]


def encode_rot13(text: str) -> str:
    return codecs.encode(text, "rot_13")


def encode_atbash(text: str) -> str:
    mapped = []
    for ch in text:
        if "a" <= ch <= "z":
            mapped.append(chr(ord("z") - (ord(ch) - ord("a"))))
        elif "A" <= ch <= "Z":
            mapped.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        else:
            mapped.append(ch)
    return "".join(mapped)


def encode_reverse(text: str) -> str:
    return text[::-1]


def _try_atbash(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    mapped = []
    for ch in text:
        if "a" <= ch <= "z":
            mapped.append(chr(ord("z") - (ord(ch) - ord("a"))))
        elif "A" <= ch <= "Z":
            mapped.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        else:
            mapped.append(ch)
    out_text = "".join(mapped)
    if out_text == text:
        return []
    return [DecodeResult("atbash", out_text.encode("utf-8"))]


def _try_reverse(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    out_text = text[::-1]
    if out_text == text:
        return []
    return [DecodeResult("reverse", out_text.encode("utf-8"))]


def _shift_alpha(text: str, shift: int) -> str:
    shifted = []
    for ch in text:
        if "a" <= ch <= "z":
            base = ord("a")
            shifted.append(chr((ord(ch) - base + shift) % 26 + base))
        elif "A" <= ch <= "Z":
            base = ord("A")
            shifted.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            shifted.append(ch)
    return "".join(shifted)


def _apply_fibonacci(
    text: str, seed_a: int, seed_b: int, direction: int, advance_all: bool
) -> str:
    a, b = seed_a, seed_b
    output = []
    for ch in text:
        advanced = False
        if "a" <= ch <= "z":
            shift = a % 26
            base = ord("a")
            output.append(chr((ord(ch) - base + direction * shift) % 26 + base))
            advanced = True
        elif "A" <= ch <= "Z":
            shift = a % 26
            base = ord("A")
            output.append(chr((ord(ch) - base + direction * shift) % 26 + base))
            advanced = True
        else:
            output.append(ch)
        if advanced or advance_all:
            a, b = b, a + b
    return "".join(output)


def encode_fibonacci(text: str, seed_a: int, seed_b: int, advance_all: bool) -> str:
    return _apply_fibonacci(text, seed_a, seed_b, 1, advance_all)


def _try_caesar(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    results = []
    for shift in range(1, 26):
        out_text = _shift_alpha(text, -shift)
        if out_text == text:
            continue
        results.append(
            DecodeResult("caesar", out_text.encode("utf-8"), note=f"shift={shift}")
        )
    return results


def encode_caesar(text: str, shift: int) -> str:
    return _shift_alpha(text, shift)


def _try_fibonacci(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    if not any(ch.isalpha() for ch in text):
        return []
    results = []
    for seed_a, seed_b in ((0, 1), (1, 1)):
        for direction, label in ((-1, "sub"), (1, "add")):
            for advance_all, adv_label in ((False, "alpha"), (True, "all")):
                out_text = _apply_fibonacci(
                    text, seed_a, seed_b, direction, advance_all
                )
                if out_text == text:
                    continue
                results.append(
                    DecodeResult(
                        "fibonacci",
                        out_text.encode("utf-8"),
                        note=f"seed={seed_a},{seed_b} dir={label} adv={adv_label}",
                    )
                )
    return results


def _try_morse(text: str, _data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    if not raw:
        return []
    for ch in raw:
        if ch not in ".-/ \t\r\n":
            return []
    normalized = raw.replace("/", " / ")
    tokens = normalized.split()
    if not tokens:
        return []
    words = []
    current = []
    for token in tokens:
        if token == "/":
            if current:
                words.append("".join(current))
                current = []
            continue
        letter = _MORSE_TABLE.get(token)
        if letter is None:
            return []
        current.append(letter)
    if current:
        words.append("".join(current))
    if not words:
        return []
    out_text = " ".join(words)
    return [DecodeResult("morse", out_text.encode("utf-8"))]


def encode_morse(text: str) -> str:
    tokens = []
    for ch in text:
        if ch.isspace():
            tokens.append("/")
            continue
        key = _MORSE_REVERSE.get(ch.upper())
        if key is None:
            raise ValueError(f"Unsupported char for morse: {ch}")
        tokens.append(key)
    output = " ".join(tokens)
    return " ".join(output.split())


def _try_bacon(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip()).upper()
    if not raw:
        return []
    if any(ch not in "AB" for ch in raw):
        return []
    if len(raw) % 5 != 0:
        return []
    results = []
    for label, mapping in (("classic", _BACON_24), ("binary", _BACON_26)):
        out_chars = []
        valid = True
        for idx in range(0, len(raw), 5):
            chunk = raw[idx : idx + 5]
            letter = mapping.get(chunk)
            if letter is None:
                valid = False
                break
            if label == "classic":
                if letter == "I":
                    out_chars.append("I/J")
                elif letter == "U":
                    out_chars.append("U/V")
                else:
                    out_chars.append(letter)
            else:
                out_chars.append(letter)
        if valid:
            out_text = "".join(out_chars)
            results.append(
                DecodeResult("bacon", out_text.encode("utf-8"), note=label)
            )
    return results


def encode_bacon(text: str, variant: str) -> str:
    if variant == "classic":
        mapping = _BACON_24_REVERSE
    elif variant == "binary":
        mapping = _BACON_26_REVERSE
    else:
        raise ValueError("Unknown bacon variant")
    output = []
    for ch in text:
        if ch.isspace():
            continue
        letter = ch.upper()
        if letter == "J" and variant == "classic":
            letter = "I"
        if letter == "V" and variant == "classic":
            letter = "U"
        if letter not in mapping:
            raise ValueError(f"Unsupported char for bacon: {ch}")
        output.append(mapping[letter])
    return " ".join(output)


def _try_polybius(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if not raw:
        return []
    if any(ch not in "12345" for ch in raw):
        return []
    if len(raw) % 2 != 0:
        return []
    out_chars = []
    for idx in range(0, len(raw), 2):
        pair = raw[idx : idx + 2]
        if pair == "24":
            out_chars.append("I/J")
            continue
        letter = _POLYBIUS.get(pair)
        if letter is None:
            return []
        out_chars.append(letter)
    out_text = "".join(out_chars)
    return [DecodeResult("polybius", out_text.encode("utf-8"), note="ij=24")]


def encode_polybius(text: str) -> str:
    output = []
    for ch in text:
        if ch.isspace():
            continue
        letter = ch.upper()
        if letter == "J":
            letter = "I"
        pair = _POLYBIUS_REVERSE.get(letter)
        if pair is None:
            raise ValueError(f"Unsupported char for polybius: {ch}")
        output.append(pair)
    return " ".join(output)


def _rail_fence_decrypt(text: str, rails: int) -> str:
    if rails <= 1:
        return text
    pattern = []
    rail = 0
    direction = 1
    for _ in range(len(text)):
        pattern.append(rail)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction

    counts = [pattern.count(r) for r in range(rails)]
    rails_chars = []
    idx = 0
    for count in counts:
        rails_chars.append(list(text[idx : idx + count]))
        idx += count

    positions = [0] * rails
    output = []
    for rail in pattern:
        output.append(rails_chars[rail][positions[rail]])
        positions[rail] += 1
    return "".join(output)


def _rail_fence_encrypt(text: str, rails: int) -> str:
    if rails <= 1:
        return text
    lines = [[] for _ in range(rails)]
    rail = 0
    direction = 1
    for ch in text:
        lines[rail].append(ch)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    return "".join("".join(line) for line in lines)


def encode_railfence(text: str, rails: int) -> str:
    return _rail_fence_encrypt(text, rails)


def _try_rail_fence(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    results = []
    limit = min(7, len(text))
    for rails in range(2, limit):
        out_text = _rail_fence_decrypt(text, rails)
        if out_text == text:
            continue
        results.append(
            DecodeResult("railfence", out_text.encode("utf-8"), note=f"rails={rails}")
        )
    return results


def _scytale_decrypt(text: str, cols: int) -> str:
    if cols <= 1:
        return text
    length = len(text)
    rows = (length + cols - 1) // cols
    full_cols = length % cols
    if full_cols == 0:
        full_cols = cols
    col_lengths = [rows if idx < full_cols else rows - 1 for idx in range(cols)]

    columns = []
    idx = 0
    for col_len in col_lengths:
        columns.append(text[idx : idx + col_len])
        idx += col_len

    output = []
    for row in range(rows):
        for col in range(cols):
            if row < len(columns[col]):
                output.append(columns[col][row])
    return "".join(output)


def _scytale_encrypt(text: str, cols: int) -> str:
    if cols <= 1:
        return text
    rows = (len(text) + cols - 1) // cols
    grid = [text[i * cols : (i + 1) * cols] for i in range(rows)]
    out = []
    for col in range(cols):
        for row in range(rows):
            if col < len(grid[row]):
                out.append(grid[row][col])
    return "".join(out)


def encode_scytale(text: str, cols: int) -> str:
    return _scytale_encrypt(text, cols)


def _try_scytale(text: str, _data: bytes) -> List[DecodeResult]:
    if not text:
        return []
    results = []
    limit = min(7, len(text))
    for cols in range(2, limit):
        out_text = _scytale_decrypt(text, cols)
        if out_text == text:
            continue
        results.append(
            DecodeResult("scytale", out_text.encode("utf-8"), note=f"cols={cols}")
        )
    return results


def _try_xor(_text: str, data: bytes) -> List[DecodeResult]:
    if not data:
        return []
    results = []
    for key in range(1, 256):
        out = bytes(byte ^ key for byte in data)
        results.append(DecodeResult("xor", out, note=f"key=0x{key:02x}"))
    return results


def _try_gzip(_text: str, data: bytes) -> List[DecodeResult]:
    if not data:
        return []
    try:
        out = gzip.decompress(data)
    except (OSError, EOFError):
        return []
    return [DecodeResult("gzip", out)]


def _try_zlib(_text: str, data: bytes) -> List[DecodeResult]:
    if not data:
        return []
    try:
        out = zlib.decompress(data)
    except (zlib.error, EOFError):
        return []
    return [DecodeResult("zlib", out)]


def _try_jwt(text: str, _data: bytes) -> List[DecodeResult]:
    raw = text.strip()
    parts = raw.split(".")
    if len(parts) < 2:
        return []
    results = []
    labels = ["jwt_header", "jwt_payload"]
    for idx, part in enumerate(parts[:2]):
        if not part:
            continue
        padded = pad_to_multiple(part, 4, "=")
        try:
            out = base64.urlsafe_b64decode(padded)
        except (binascii.Error, ValueError):
            continue
        results.append(DecodeResult("jwt", out, note=labels[idx]))
    return results


def get_decoders() -> List[Decoder]:
    return [
        Decoder("hex", "hex string to bytes", _try_hex),
        Decoder("base64", "base64 decode", _try_base64),
        Decoder("base64url", "urlsafe base64 decode", _try_base64url),
        Decoder("base32", "base32 decode", _try_base32),
        Decoder("base85", "base85 decode", _try_base85),
        Decoder("ascii85", "ascii85 decode", _try_ascii85),
        Decoder("base58", "base58 decode", _try_base58),
        Decoder("url", "url percent decode", _try_url),
        Decoder("rot13", "rot13 transform", _try_rot13),
        Decoder("caesar", "caesar shifts", _try_caesar),
        Decoder("fibonacci", "fibonacci shift cipher", _try_fibonacci),
        Decoder("atbash", "atbash substitution", _try_atbash),
        Decoder("reverse", "reverse characters", _try_reverse),
        Decoder("morse", "morse code decode", _try_morse),
        Decoder("bacon", "bacon cipher decode", _try_bacon),
        Decoder("polybius", "polybius square decode", _try_polybius),
        Decoder("railfence", "rail fence transposition", _try_rail_fence),
        Decoder("scytale", "scytale transposition", _try_scytale),
        Decoder("xor", "single-byte xor brute force", _try_xor),
        Decoder("gzip", "gzip decompress", _try_gzip),
        Decoder("zlib", "zlib decompress", _try_zlib),
        Decoder("jwt", "jwt header/payload decode", _try_jwt),
    ]


def get_encoders() -> List[Encoder]:
    return [
        Encoder("hex", "hex encode", encode_hex),
        Encoder("base64", "base64 encode", encode_base64),
        Encoder("base64url", "urlsafe base64 encode", encode_base64url),
        Encoder("base32", "base32 encode", encode_base32),
        Encoder("base85", "base85 encode", encode_base85),
        Encoder("ascii85", "ascii85 encode", encode_ascii85),
        Encoder("base58", "base58 encode", encode_base58),
        Encoder("url", "url percent encode", encode_url),
        Encoder("rot13", "rot13 transform", encode_rot13),
        Encoder("caesar", "caesar shift encode"),
        Encoder("fibonacci", "fibonacci shift encode"),
        Encoder("atbash", "atbash substitution", encode_atbash),
        Encoder("reverse", "reverse characters", encode_reverse),
        Encoder("bacon", "bacon cipher encode"),
        Encoder("polybius", "polybius square encode"),
        Encoder("morse", "morse code encode"),
        Encoder("railfence", "rail fence transposition encode"),
        Encoder("scytale", "scytale transposition encode"),
    ]
