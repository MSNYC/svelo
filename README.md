# svelo

Lightweight CLI that tries common decoders on a string and can also encode.

## Install (local)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Usage

Interactive menu (recommended for tricky inputs):

```bash
svelo
```

```bash
svelo "SGVsbG8gV29ybGQh"
```

Encode (interactive):

```bash
svelo --encode "Hello World"
```

Encode with paste mode (safe for quotes/backticks):

```bash
svelo --encode --paste
```

Encode (non-interactive):

```bash
svelo --encode --encoder hex "Hello World"
```

Read from stdin:

```bash
echo "48656c6c6f" | svelo
```

List decoders:

```bash
svelo --list
```

List encoders:

```bash
svelo --list-encoders
```

Try multiple decode layers:

```bash
svelo --chain-depth 2 "H4sIAAAAA..."
```

Rank by improvement vs input:

```bash
svelo --rank delta --top 3 "Gur pbpx pebjf ng qnja."
```

## Interactive menu

The interactive menu is split into four modes:

- Decode: non-keyed decoders (formats and simple transforms)
- Decrypt: keyed ciphers (you supply keys and can retry)
- Encode: non-keyed encoders
- Encrypt: keyed ciphers (you supply keys)

In Decrypt mode, you select a keyed cipher and keep trying keys until you
copy a successful result or return to the menu.

## Included decoders

- hex, binary, base64, base64url, base32, base85, ascii85, base58, url
- rot13, caesar, fibonacci, atbash, reverse, bacon, polybius, morse, railfence, scytale, xor
- vigenere, beaufort, variant, autokey, keyword, columnar, playfair, hill, adfgx, adfgvx (interactive encrypt/decrypt)
- gzip, zlib, jwt

## Options

- `--list` list available decoders
- `--list-encoders` list available encoders
- `--encode` encode input (prompts for cipher)
- `--interactive` launch interactive menu
- `--paste` read input from stdin (safe for quotes/backticks)
- `--encoder` encoder to use in encode mode (skips prompt)
- `--decoder` run specific decoders only (repeatable)
- `--chain-depth` number of decode passes to attempt
- `--min-score` filter low-confidence results by absolute score (0-1)
- `--min-delta` filter outputs that do not improve vs input
- `--top` show only the top N ranked results
- `--rank` ranking mode: absolute, delta, or both
- `--max-per-decoder` cap results per decoder family (0 = no cap)
- `--all` show all results (ignore filters and top)
- `--max-results` stop after N results
- `--show-hex` include hex output
- `--max-chars` truncate long outputs (0 = no limit)
- `--color` color output: auto, always, or never
- `--railfence-strip-spaces` strip spaces before rail fence encoding
- `--key` key for keyed ciphers in encrypt mode (non-interactive)
- `--key2` second key for ADFGX/ADFGVX in encrypt mode (non-interactive)

## Keyed ciphers

Keyed ciphers (vigenere, beaufort, variant, autokey, keyword, columnar, playfair, hill, adfgx, adfgvx)
are available in the interactive encrypt/decrypt flows, where you can supply keys and retry.
In non-interactive encrypt mode, provide `--key` (and `--key2` for ADFGX/ADFGVX).

## Cipher conventions

To make results reproducible across tools, `svelo` uses explicit conventions:

- vigenere/beaufort/variant/autokey: key is letters A-Z only; key advances on letters; non-letters are preserved; case is preserved.
- keyword substitution: key is letters A-Z only; non-letters preserved; case preserved.
- columnar transposition: key is letters A-Z only; all characters (including spaces) are transposed.
- playfair: letters only with J->I; output is uppercase letters, no spacing or punctuation; uses X as filler.
- hill (2x2): key is exactly 4 letters; text uses letters only; pads with X.
- adfgx: letters only with J->I; uses ADFGX digraphs, then columnar transposition.
- adfgvx: letters/digits only; uses ADFGVX digraphs, then columnar transposition.

## Rail fence variants

Rail fence output can depend on whether spaces are kept as characters or stripped first.
This tool supports both and labels decode results accordingly (e.g. `rails=3,stripspaces=yes`).

## Notes

This tool avoids external dependencies by using the Python standard library only.

## Disclaimer

This project is for educational and informational purposes only and is provided "as is" without warranty.
Do not rely on it for security-critical or irreversible data without independent verification.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Issues

Report bugs or request features at `https://github.com/MSNYC/Svelo/issues`.
