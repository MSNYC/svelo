# svelo

**A lightweight educational CLI for classical cryptography and encoding**

Svelo helps you decode and encode text using classical ciphers and common encodings. Perfect for CTF challenges, learning cryptography, or exploring historical cipher techniques.

## Mission

This project aims to be more than just a decoder tool—it's growing into a comprehensive educational resource for cryptography. We're building:

- **Learning-focused features**: Explanations, tutorials, and cipher background
- **Interactive exploration**: Hands-on cipher experimentation
- **Community-driven growth**: Open to contributions and ideas

See our [ROADMAP.md](ROADMAP.md) for planned features like an in-app glossary, cryptanalysis tools, and educational tutorials.

## Install (local)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Usage

### Quick Start (Interactive Mode - Recommended!)

Just run `svelo` to launch the interactive menu:

```bash
svelo
```

This gives you a guided experience with:
- **Decode** - Try all decoders automatically on your input
- **Decrypt** - Use keyed ciphers (Vigenère, Playfair, etc.) with retry
- **Encode** - Convert plaintext to encodings
- **Encrypt** - Use keyed ciphers to encrypt
- **Learn** - Browse the cipher glossary with 33 detailed entries
- **Help** - Reference guide for all features

The interactive mode handles special characters safely and guides you through each step.

### Quick Decode (Command Line)

For quick decodes, pass the encoded text directly:

```bash
svelo "SGVsbG8gV29ybGQh"
# Auto-tries all decoders and shows ranked results
```

Read from stdin:

```bash
echo "48656c6c6f" | svelo
```

### Learn About Ciphers

View detailed information about any cipher:

```bash
svelo --info vigenere
svelo --info caesar
svelo --info playfair
```

Each entry includes how it works, historical context, security level, and learning resources.

### Quick Encode

Encode text interactively:

```bash
svelo --encode "Hello World"
# Prompts you to choose an encoder
```

Or specify the encoder directly:

```bash
svelo --encode --encoder hex "Hello World"
# Output: 48656c6c6f20576f726c64
```

### Advanced Command-Line Options

List available decoders/encoders:

```bash
svelo --list
svelo --list-encoders
```

Try multiple decode layers (chained decoding):

```bash
svelo --chain-depth 2 "H4sIAAAAA..."
```

Show only top results:

```bash
svelo --top 5 "encoded_text"
```

Rank by improvement vs input:

```bash
svelo --rank delta --top 3 "Gur pbpx pebjf ng qnja."
```

For a complete list of options, see the [Options](#options) section below.

## Interactive menu

The interactive menu provides guided workflows:

- **Decode**: non-keyed decoders (formats and simple transforms)
- **Decrypt**: keyed ciphers (you supply keys and can retry)
- **Encode**: non-keyed encoders
- **Encrypt**: keyed ciphers (you supply keys)
- **Learn**: cipher glossary with descriptions, history, and references

In Decrypt mode, you select a keyed cipher and keep trying keys until you
copy a successful result or return to the menu. In Learn mode, browse or search
ciphers to understand how they work and their historical context.

## Included decoders

- hex, binary, base64, base64url, base32, base85, ascii85, base58, url
- rot13, caesar, fibonacci, atbash, reverse, bacon, polybius, morse, railfence, scytale, xor
- vigenere, beaufort, variant, autokey, keyword, columnar, playfair, hill, adfgx, adfgvx (interactive encrypt/decrypt)
- gzip, zlib, jwt

## Options

- `--list` list available decoders
- `--list-encoders` list available encoders
- `--info CIPHER` show glossary entry for a cipher
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

**Note:** Most users will prefer the interactive menu (`svelo` with no arguments) which handles all of these options with guided prompts. The command-line flags above are for scripting and advanced use cases.

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

Run the test suite:

```bash
pip install -e ".[dev]"
pytest
```

**Test Coverage:**

The project includes comprehensive tests for core cryptographic functionality:

- ✅ **All cipher algorithms** - Thoroughly tested with roundtrip tests and known outputs
- ✅ **All encoders/decoders** - Verified against standard implementations
- ✅ **Basic CLI flags** - `--list`, `--encode`, `--decoder`, `--info`, stdin input
- ✅ **Glossary system** - Verified `--info` flag returns correct entries

**Not Currently Tested:**

- Interactive menu workflows (manually tested)
- Some advanced CLI flags (`--chain-depth`, `--min-score`, `--rank`, etc.)
- Learn menu browse/search functionality (manually tested)

The cryptographic implementations are the most critical components and are thoroughly tested.
Interactive features have been manually verified to work correctly.

## Contributing

Contributions are welcome! We're especially interested in:

- **New ciphers and encodings**: Add support for additional cryptographic techniques
- **Educational content**: Glossary entries, explanations, historical context
- **Analysis features**: Frequency analysis, cipher detection, cryptanalysis tools
- **Documentation**: Tutorials, examples, and learning resources
- **Bug fixes and improvements**: Better accuracy, performance, or UX

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [ROADMAP.md](ROADMAP.md) for planned features.

**Quick Start for Contributors:**
1. Fork the repository
2. Create a feature branch
3. Make your changes (add tests!)
4. Open a pull request

## Roadmap

We're actively expanding Svelo into a comprehensive cryptography education tool. Planned features include:

- **Glossary system**: In-app explanations with reference links for each cipher
- **Cryptanalysis tools**: Frequency analysis, pattern detection, cipher identification
- **Tutorial mode**: Interactive lessons on how ciphers work
- **Historical context**: Background on when/where ciphers were used
- **Additional ciphers**: Four-square, bifid, trifid, and more

See the full [ROADMAP.md](ROADMAP.md) for details and status.

## Issues & Feedback

- **Bug reports**: [Open an issue](https://github.com/MSNYC/Svelo/issues)
- **Feature requests**: Share your ideas in [Issues](https://github.com/MSNYC/Svelo/issues)
- **Questions**: Start a discussion or open an issue
- **Educational ideas**: We'd love to hear about cipher resources or teaching opportunities

## License

MIT License - see [LICENSE](LICENSE) for details.
