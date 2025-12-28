import base64
import gzip
import zlib

from svelo.decoders import get_decoders


def _decoder_by_name(name: str):
    decoders = {decoder.name: decoder for decoder in get_decoders()}
    return decoders[name]


def test_hex_decode():
    decoder = _decoder_by_name("hex")
    results = decoder.func("48656c6c6f", b"48656c6c6f")
    assert len(results) == 1
    assert results[0].output == b"Hello"


def test_base64_decode():
    decoder = _decoder_by_name("base64")
    results = decoder.func("SGVsbG8=", b"SGVsbG8=")
    assert len(results) == 1
    assert results[0].output == b"Hello"


def test_atbash_decode():
    decoder = _decoder_by_name("atbash")
    results = decoder.func("Svool", b"Svool")
    assert len(results) == 1
    assert results[0].output == b"Hello"


def test_reverse_decode():
    decoder = _decoder_by_name("reverse")
    results = decoder.func("stressed", b"stressed")
    assert len(results) == 1
    assert results[0].output == b"desserts"


def _fibonacci_encode(
    text: str, seed_a: int, seed_b: int, advance_all: bool
) -> str:
    a, b = seed_a, seed_b
    output = []
    for ch in text:
        advanced = False
        if "a" <= ch <= "z":
            shift = a % 26
            base = ord("a")
            output.append(chr((ord(ch) - base + shift) % 26 + base))
            advanced = True
        elif "A" <= ch <= "Z":
            shift = a % 26
            base = ord("A")
            output.append(chr((ord(ch) - base + shift) % 26 + base))
            advanced = True
        else:
            output.append(ch)
        if advanced or advance_all:
            a, b = b, a + b
    return "".join(output)


def test_fibonacci_decode():
    decoder = _decoder_by_name("fibonacci")
    plaintext = "HELLO"
    cipher = _fibonacci_encode(plaintext, 0, 1, False)
    results = decoder.func(cipher, cipher.encode("utf-8"))
    assert any(result.output == plaintext.encode("utf-8") for result in results)


def test_fibonacci_decode_advances_on_all_chars():
    decoder = _decoder_by_name("fibonacci")
    plaintext = "The cock crows at dawn"
    cipher = _fibonacci_encode(plaintext, 0, 1, True)
    results = decoder.func(cipher, cipher.encode("utf-8"))
    assert any(result.output == plaintext.encode("utf-8") for result in results)


def test_morse_decode():
    decoder = _decoder_by_name("morse")
    results = decoder.func(
        ".... . .-.. .-.. --- / .-- --- .-. .-.. -..",
        b".... . .-.. .-.. --- / .-- --- .-. .-.. -..",
    )
    assert len(results) == 1
    assert results[0].output == b"HELLO WORLD"


def test_bacon_decode():
    decoder = _decoder_by_name("bacon")
    results = decoder.func("BBAAB", b"BBAAB")
    outputs = {result.output for result in results}
    assert b"Z" in outputs


def test_polybius_decode():
    decoder = _decoder_by_name("polybius")
    results = decoder.func("2315313134", b"2315313134")
    assert len(results) == 1
    assert results[0].output == b"HELLO"


def _scytale_encrypt(text: str, cols: int) -> str:
    rows = (len(text) + cols - 1) // cols
    grid = [text[i * cols : (i + 1) * cols] for i in range(rows)]
    out = []
    for col in range(cols):
        for row in range(rows):
            if col < len(grid[row]):
                out.append(grid[row][col])
    return "".join(out)


def test_rail_fence_decode():
    decoder = _decoder_by_name("railfence")
    cipher = "WECRLTEERDSOEEFEAOCAIVDEN"
    results = decoder.func(cipher, cipher.encode("utf-8"))
    matches = [result for result in results if result.note == "rails=3"]
    assert any(result.output == b"WEAREDISCOVEREDFLEEATONCE" for result in matches)


def test_scytale_decode():
    decoder = _decoder_by_name("scytale")
    plain = "WEAREDISCOVEREDFLEEATONCE"
    cipher = _scytale_encrypt(plain, 5)
    results = decoder.func(cipher, cipher.encode("utf-8"))
    matches = [result for result in results if result.note == "cols=5"]
    assert any(result.output == plain.encode("utf-8") for result in matches)


def test_xor_decode():
    decoder = _decoder_by_name("xor")
    plaintext = b"Hello"
    key = 0x2A
    cipher = bytes(byte ^ key for byte in plaintext)
    results = decoder.func(cipher.decode("latin1"), cipher)
    assert any(result.output == plaintext for result in results)


def test_url_decode():
    decoder = _decoder_by_name("url")
    results = decoder.func("Hello%20World", b"Hello%20World")
    assert len(results) == 1
    assert results[0].output == b"Hello World"


def test_gzip_decode():
    decoder = _decoder_by_name("gzip")
    payload = gzip.compress(b"Hello gzip")
    results = decoder.func(payload.decode("latin1"), payload)
    assert len(results) == 1
    assert results[0].output == b"Hello gzip"


def test_zlib_decode():
    decoder = _decoder_by_name("zlib")
    payload = zlib.compress(b"Hello zlib")
    results = decoder.func(payload.decode("latin1"), payload)
    assert len(results) == 1
    assert results[0].output == b"Hello zlib"


def test_jwt_decode():
    decoder = _decoder_by_name("jwt")
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=")
    payload = base64.urlsafe_b64encode(b'{"sub":"123"}').rstrip(b"=")
    token = b".".join([header, payload, b"sig"])
    results = decoder.func(token.decode("ascii"), token)
    assert len(results) == 2
    assert results[0].output == b'{"alg":"none"}'
    assert results[1].output == b'{"sub":"123"}'
