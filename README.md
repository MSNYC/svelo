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

## Included decoders

- hex, base64, base64url, base32, base85, ascii85, base58, url
- rot13, caesar, fibonacci, atbash, reverse, bacon, polybius, morse, railfence, scytale, xor
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

## Notes

This tool avoids external dependencies by using the Python standard library only.

## Tests

```bash
pip install -e ".[dev]"
pytest
```
