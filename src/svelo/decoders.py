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


def _clean_key_alpha(key: str) -> str:
    cleaned = "".join(ch for ch in key.upper() if "A" <= ch <= "Z")
    if not cleaned:
        raise ValueError("Key must contain at least one letter A-Z.")
    return cleaned


def _alpha_index(ch: str) -> int:
    return ord(ch) - ord("A")


def _shift_alpha_char(ch: str, shift: int) -> str:
    if "a" <= ch <= "z":
        return chr((ord(ch) - ord("a") + shift) % 26 + ord("a"))
    if "A" <= ch <= "Z":
        return chr((ord(ch) - ord("A") + shift) % 26 + ord("A"))
    return ch


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


def _try_binary(text: str, _data: bytes) -> List[DecodeResult]:
    raw = clean_whitespace(text.strip())
    if not raw:
        return []
    if any(ch not in "01" for ch in raw):
        return []
    if len(raw) % 8 != 0:
        return []
    out = bytearray()
    for idx in range(0, len(raw), 8):
        out.append(int(raw[idx : idx + 8], 2))
    return [DecodeResult("binary", bytes(out))]


def encode_hex(text: str) -> str:
    return text.encode("utf-8").hex()


def encode_binary(text: str) -> str:
    return " ".join(format(byte, "08b") for byte in text.encode("utf-8"))


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


def _vigenere_key_stream(text: str, key: str) -> List[int]:
    shifts = [_alpha_index(ch) for ch in _clean_key_alpha(key)]
    stream = []
    idx = 0
    for ch in text:
        if ch.isalpha():
            stream.append(shifts[idx % len(shifts)])
            idx += 1
        else:
            stream.append(0)
    return stream


def vigenere_encrypt(text: str, key: str) -> str:
    shifts = _vigenere_key_stream(text, key)
    out = []
    for ch, shift in zip(text, shifts):
        if ch.isalpha():
            out.append(_shift_alpha_char(ch, shift))
        else:
            out.append(ch)
    return "".join(out)


def vigenere_decrypt(text: str, key: str) -> str:
    shifts = _vigenere_key_stream(text, key)
    out = []
    for ch, shift in zip(text, shifts):
        if ch.isalpha():
            out.append(_shift_alpha_char(ch, -shift))
        else:
            out.append(ch)
    return "".join(out)


def beaufort_encrypt(text: str, key: str) -> str:
    shifts = _vigenere_key_stream(text, key)
    out = []
    for ch, shift in zip(text, shifts):
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            idx = ord(ch) - base
            out.append(chr((shift - idx) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def beaufort_decrypt(text: str, key: str) -> str:
    return beaufort_encrypt(text, key)


def variant_beaufort_encrypt(text: str, key: str) -> str:
    shifts = _vigenere_key_stream(text, key)
    out = []
    for ch, shift in zip(text, shifts):
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            idx = ord(ch) - base
            out.append(chr((idx - shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def variant_beaufort_decrypt(text: str, key: str) -> str:
    shifts = _vigenere_key_stream(text, key)
    out = []
    for ch, shift in zip(text, shifts):
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            idx = ord(ch) - base
            out.append(chr((shift + idx) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def autokey_encrypt(text: str, key: str) -> str:
    key_clean = _clean_key_alpha(key)
    out = []
    key_stream = list(key_clean)
    for ch in text:
        if ch.isalpha():
            shift = _alpha_index(key_stream.pop(0))
            out.append(_shift_alpha_char(ch, shift))
            key_stream.append(ch.upper())
        else:
            out.append(ch)
    return "".join(out)


def autokey_decrypt(text: str, key: str) -> str:
    key_stream = list(_clean_key_alpha(key))
    out = []
    for ch in text:
        if ch.isalpha():
            shift = _alpha_index(key_stream.pop(0))
            plain = _shift_alpha_char(ch, -shift)
            out.append(plain)
            key_stream.append(plain.upper())
        else:
            out.append(ch)
    return "".join(out)


def keyword_substitution_encrypt(text: str, key: str) -> str:
    key_clean = _clean_key_alpha(key)
    seen = set()
    alphabet = []
    for ch in key_clean:
        if ch not in seen:
            seen.add(ch)
            alphabet.append(ch)
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            alphabet.append(ch)
    mapping = {plain: subst for plain, subst in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", alphabet)}
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(mapping[ch])
        elif "a" <= ch <= "z":
            out.append(mapping[ch.upper()].lower())
        else:
            out.append(ch)
    return "".join(out)


def keyword_substitution_decrypt(text: str, key: str) -> str:
    key_clean = _clean_key_alpha(key)
    seen = set()
    alphabet = []
    for ch in key_clean:
        if ch not in seen:
            seen.add(ch)
            alphabet.append(ch)
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            alphabet.append(ch)
    inverse = {subst: plain for plain, subst in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", alphabet)}
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(inverse[ch])
        elif "a" <= ch <= "z":
            out.append(inverse[ch.upper()].lower())
        else:
            out.append(ch)
    return "".join(out)


def _columnar_key_order(key: str) -> List[int]:
    key_clean = _clean_key_alpha(key)
    indexed = list(enumerate(key_clean))
    sorted_cols = sorted(indexed, key=lambda item: (item[1], item[0]))
    order = [idx for idx, _ in sorted_cols]
    return order


def columnar_encrypt(text: str, key: str) -> str:
    order = _columnar_key_order(key)
    cols = len(order)
    rows = (len(text) + cols - 1) // cols
    grid = [text[i * cols : (i + 1) * cols] for i in range(rows)]
    output = []
    for col in order:
        for row in range(rows):
            if col < len(grid[row]):
                output.append(grid[row][col])
    return "".join(output)


def columnar_decrypt(text: str, key: str) -> str:
    order = _columnar_key_order(key)
    cols = len(order)
    if cols == 0:
        return text
    rows = (len(text) + cols - 1) // cols
    remainder = len(text) % cols
    if remainder == 0:
        remainder = cols
    # Determine which original column positions have full length
    col_lengths = [rows if idx < remainder else rows - 1 for idx in range(cols)]
    columns = [""] * cols
    idx = 0
    for col in order:
        length = col_lengths[col]
        columns[col] = text[idx : idx + length]
        idx += length
    output = []
    for row in range(rows):
        for col in range(cols):
            if row < len(columns[col]):
                output.append(columns[col][row])
    return "".join(output)


def _playfair_square(key: str) -> List[List[str]]:
    key_clean = _clean_key_alpha(key).replace("J", "I")
    seen = set()
    letters = []
    for ch in key_clean:
        if ch not in seen:
            seen.add(ch)
            letters.append(ch)
    for ch in "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            letters.append(ch)
    square = [letters[i * 5 : (i + 1) * 5] for i in range(5)]
    return square


def _playfair_positions(square: List[List[str]]) -> dict:
    positions = {}
    for r, row in enumerate(square):
        for c, ch in enumerate(row):
            positions[ch] = (r, c)
    return positions


def _playfair_digraphs(text: str) -> List[str]:
    raw = "".join(ch for ch in text.upper() if "A" <= ch <= "Z").replace("J", "I")
    pairs = []
    idx = 0
    while idx < len(raw):
        a = raw[idx]
        b = raw[idx + 1] if idx + 1 < len(raw) else "X"
        if a == b:
            pairs.append(a + "X")
            idx += 1
        else:
            pairs.append(a + b)
            idx += 2
    if pairs and len(pairs[-1]) == 1:
        pairs[-1] = pairs[-1] + "X"
    return pairs


def playfair_encrypt(text: str, key: str) -> str:
    square = _playfair_square(key)
    positions = _playfair_positions(square)
    out = []
    for pair in _playfair_digraphs(text):
        a, b = pair[0], pair[1]
        ra, ca = positions[a]
        rb, cb = positions[b]
        if ra == rb:
            out.append(square[ra][(ca + 1) % 5])
            out.append(square[rb][(cb + 1) % 5])
        elif ca == cb:
            out.append(square[(ra + 1) % 5][ca])
            out.append(square[(rb + 1) % 5][cb])
        else:
            out.append(square[ra][cb])
            out.append(square[rb][ca])
    return "".join(out)


def playfair_decrypt(text: str, key: str) -> str:
    square = _playfair_square(key)
    positions = _playfair_positions(square)
    raw = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    if len(raw) % 2 != 0:
        raw = raw + "X"
    out = []
    for idx in range(0, len(raw), 2):
        a, b = raw[idx], raw[idx + 1]
        ra, ca = positions[a]
        rb, cb = positions[b]
        if ra == rb:
            out.append(square[ra][(ca - 1) % 5])
            out.append(square[rb][(cb - 1) % 5])
        elif ca == cb:
            out.append(square[(ra - 1) % 5][ca])
            out.append(square[(rb - 1) % 5][cb])
        else:
            out.append(square[ra][cb])
            out.append(square[rb][ca])
    return "".join(out)


def _hill_matrix_from_key(key: str) -> List[List[int]]:
    key_clean = _clean_key_alpha(key)
    if len(key_clean) != 4:
        raise ValueError("Hill cipher key must be exactly 4 letters.")
    values = [_alpha_index(ch) for ch in key_clean]
    return [[values[0], values[1]], [values[2], values[3]]]


def _modinv(value: int, modulus: int) -> int:
    value %= modulus
    for i in range(1, modulus):
        if (value * i) % modulus == 1:
            return i
    raise ValueError("Key matrix is not invertible under mod 26.")


def hill_encrypt(text: str, key: str) -> str:
    matrix = _hill_matrix_from_key(key)
    raw = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    if len(raw) % 2 != 0:
        raw += "X"
    out = []
    for idx in range(0, len(raw), 2):
        a = _alpha_index(raw[idx])
        b = _alpha_index(raw[idx + 1])
        c0 = (matrix[0][0] * a + matrix[0][1] * b) % 26
        c1 = (matrix[1][0] * a + matrix[1][1] * b) % 26
        out.append(chr(c0 + ord("A")))
        out.append(chr(c1 + ord("A")))
    return "".join(out)


def hill_decrypt(text: str, key: str) -> str:
    matrix = _hill_matrix_from_key(key)
    det = (matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) % 26
    inv_det = _modinv(det, 26)
    inv = [
        [(matrix[1][1] * inv_det) % 26, (-matrix[0][1] * inv_det) % 26],
        [(-matrix[1][0] * inv_det) % 26, (matrix[0][0] * inv_det) % 26],
    ]
    raw = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    if len(raw) % 2 != 0:
        raw += "X"
    out = []
    for idx in range(0, len(raw), 2):
        a = _alpha_index(raw[idx])
        b = _alpha_index(raw[idx + 1])
        p0 = (inv[0][0] * a + inv[0][1] * b) % 26
        p1 = (inv[1][0] * a + inv[1][1] * b) % 26
        out.append(chr(p0 + ord("A")))
        out.append(chr(p1 + ord("A")))
    return "".join(out)


def _adfgx_square(key: str) -> dict:
    key_clean = _clean_key_alpha(key).replace("J", "I")
    seen = set()
    letters = []
    for ch in key_clean:
        if ch not in seen:
            seen.add(ch)
            letters.append(ch)
    for ch in "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            letters.append(ch)
    coords = {}
    symbols = "ADFGX"
    idx = 0
    for r in range(5):
        for c in range(5):
            coords[letters[idx]] = symbols[r] + symbols[c]
            idx += 1
    return coords


def _adfgx_reverse_square(key: str) -> dict:
    forward = _adfgx_square(key)
    return {value: k for k, value in forward.items()}


def adfgx_encrypt(text: str, square_key: str, transposition_key: str) -> str:
    coords = _adfgx_square(square_key)
    raw = "".join(ch for ch in text.upper() if "A" <= ch <= "Z").replace("J", "I")
    pairs = "".join(coords[ch] for ch in raw)
    return columnar_encrypt(pairs, transposition_key)


def adfgx_decrypt(text: str, square_key: str, transposition_key: str) -> str:
    reverse = _adfgx_reverse_square(square_key)
    pairs = columnar_decrypt(text, transposition_key)
    if len(pairs) % 2 != 0:
        pairs = pairs[:-1]
    out = []
    for idx in range(0, len(pairs), 2):
        digraph = pairs[idx : idx + 2]
        letter = reverse.get(digraph)
        if letter is None:
            raise ValueError("Invalid ADFGX digraph encountered.")
        out.append(letter)
    return "".join(out)


def _adfgvx_square(key: str) -> dict:
    key_clean = "".join(ch for ch in key.upper() if ch.isalnum())
    if not key_clean:
        raise ValueError("Key must contain at least one letter or digit.")
    seen = set()
    alphabet = []
    for ch in key_clean:
        if ch not in seen:
            seen.add(ch)
            alphabet.append(ch)
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        if ch not in seen:
            alphabet.append(ch)
    coords = {}
    symbols = "ADFGVX"
    idx = 0
    for r in range(6):
        for c in range(6):
            coords[alphabet[idx]] = symbols[r] + symbols[c]
            idx += 1
    return coords


def _adfgvx_reverse_square(key: str) -> dict:
    forward = _adfgvx_square(key)
    return {value: k for k, value in forward.items()}


def adfgvx_encrypt(text: str, square_key: str, transposition_key: str) -> str:
    coords = _adfgvx_square(square_key)
    raw = "".join(ch for ch in text.upper() if ch.isalnum())
    pairs = "".join(coords[ch] for ch in raw)
    return columnar_encrypt(pairs, transposition_key)


def adfgvx_decrypt(text: str, square_key: str, transposition_key: str) -> str:
    reverse = _adfgvx_reverse_square(square_key)
    pairs = columnar_decrypt(text, transposition_key)
    if len(pairs) % 2 != 0:
        pairs = pairs[:-1]
    out = []
    for idx in range(0, len(pairs), 2):
        digraph = pairs[idx : idx + 2]
        letter = reverse.get(digraph)
        if letter is None:
            raise ValueError("Invalid ADFGVX digraph encountered.")
        out.append(letter)
    return "".join(out)


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


def encode_railfence(text: str, rails: int, strip_spaces: bool = False) -> str:
    if strip_spaces:
        text = clean_whitespace(text)
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
            DecodeResult(
                "railfence", out_text.encode("utf-8"), note=f"rails={rails},stripspaces=no"
            )
        )
        stripped = clean_whitespace(text)
        if stripped and stripped != text:
            out_text = _rail_fence_decrypt(stripped, rails)
            if out_text != stripped:
                results.append(
                    DecodeResult(
                        "railfence",
                        out_text.encode("utf-8"),
                        note=f"rails={rails},stripspaces=yes",
                    )
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


def encode_vigenere(text: str, key: str) -> str:
    return vigenere_encrypt(text, key)


def encode_beaufort(text: str, key: str) -> str:
    return beaufort_encrypt(text, key)


def encode_variant(text: str, key: str) -> str:
    return variant_beaufort_encrypt(text, key)


def encode_autokey(text: str, key: str) -> str:
    return autokey_encrypt(text, key)


def encode_keyword_substitution(text: str, key: str) -> str:
    return keyword_substitution_encrypt(text, key)


def encode_columnar(text: str, key: str) -> str:
    return columnar_encrypt(text, key)


def encode_playfair(text: str, key: str) -> str:
    return playfair_encrypt(text, key)


def encode_hill(text: str, key: str) -> str:
    return hill_encrypt(text, key)


def encode_adfgx(text: str, square_key: str, transposition_key: str) -> str:
    return adfgx_encrypt(text, square_key, transposition_key)


def encode_adfgvx(text: str, square_key: str, transposition_key: str) -> str:
    return adfgvx_encrypt(text, square_key, transposition_key)


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
        Decoder("binary", "binary string to bytes", _try_binary),
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
        Encoder("binary", "binary encode", encode_binary),
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
        Encoder("vigenere", "vigenere cipher encode"),
        Encoder("beaufort", "beaufort cipher encode"),
        Encoder("variant", "variant beaufort cipher encode"),
        Encoder("autokey", "autokey cipher encode"),
        Encoder("keyword", "keyword substitution encode"),
        Encoder("columnar", "columnar transposition encode"),
        Encoder("playfair", "playfair cipher encode"),
        Encoder("hill", "hill cipher (2x2) encode"),
        Encoder("adfgx", "adfgx cipher encode"),
        Encoder("adfgvx", "adfgvx cipher encode"),
    ]
