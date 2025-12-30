import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from .decoders import (
    DecodeResult,
    Decoder,
    Encoder,
    adfgvx_decrypt,
    adfgx_decrypt,
    autokey_decrypt,
    beaufort_decrypt,
    columnar_decrypt,
    encode_bacon,
    encode_adfgvx,
    encode_adfgx,
    encode_autokey,
    encode_beaufort,
    encode_columnar,
    encode_caesar,
    encode_fibonacci,
    encode_hill,
    encode_keyword_substitution,
    encode_morse,
    encode_playfair,
    encode_polybius,
    encode_railfence,
    encode_scytale,
    encode_variant,
    encode_vigenere,
    get_decoders,
    get_encoders,
    hill_decrypt,
    keyword_substitution_decrypt,
    playfair_decrypt,
    variant_beaufort_decrypt,
    vigenere_decrypt,
)
from .glossary import format_entry, get_all_entries, get_entry, search_entries
from .utils import english_score, to_text

try:
    import termios
except ImportError:  # pragma: no cover - not available on all platforms
    termios = None

DEFAULT_CHAIN_DEPTH = 1
DEFAULT_MIN_SCORE = 0.25
DEFAULT_MIN_DELTA = 0.0
DEFAULT_TOP = 5
DEFAULT_RANK = "both"
DEFAULT_MAX_PER_DECODER = 1
DEFAULT_MAX_RESULTS = 50
DEFAULT_SHOW_HEX = False
DEFAULT_MAX_CHARS = 2000
DEFAULT_PAGE_SIZE = 5
INPUT_PREFIX = ">> "
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_DIM = "\033[2m"
COLOR_ENABLED = False
CLEAR_VIEW = "\033[2J\033[H"
_DECODE_METHODS = (
    "hex",
    "binary",
    "base64",
    "base64url",
    "base32",
    "base85",
    "ascii85",
    "base58",
    "url",
    "rot13",
    "caesar",
    "fibonacci",
    "atbash",
    "reverse",
    "morse",
    "bacon",
    "polybius",
    "railfence",
    "scytale",
    "xor",
    "gzip",
    "zlib",
    "jwt",
)
_KEYED_CIPHERS = {
    "vigenere": "vigenere cipher (keyed)",
    "beaufort": "beaufort cipher (keyed)",
    "variant": "variant beaufort cipher (keyed)",
    "autokey": "autokey cipher (keyed)",
    "keyword": "keyword substitution (keyed)",
    "columnar": "columnar transposition (keyed)",
    "playfair": "playfair cipher (keyed)",
    "hill": "hill cipher (2x2 key)",
    "adfgx": "adfgx cipher (square+transposition keys)",
    "adfgvx": "adfgvx cipher (square+transposition keys)",
}
_ENCODE_METHODS = (
    "hex",
    "binary",
    "base64",
    "base64url",
    "base32",
    "base85",
    "ascii85",
    "base58",
    "url",
    "rot13",
    "caesar",
    "fibonacci",
    "atbash",
    "reverse",
    "bacon",
    "polybius",
    "morse",
    "railfence",
    "scytale",
)
_ENCRYPT_METHODS = tuple(_KEYED_CIPHERS.keys())


def _style(text: str, *codes: str) -> str:
    if not COLOR_ENABLED or not codes:
        return text
    return "".join(codes) + text + COLOR_RESET


def _print_section(title: str) -> None:
    print("")
    print(_style(title, COLOR_BOLD, COLOR_CYAN))
    print(_style("=" * len(title), COLOR_DIM))
    print("")


def _clear_view() -> None:
    if not sys.stdout.isatty():
        return
    print(CLEAR_VIEW, end="")


def _prompt_line(prompt: str) -> str:
    print("")
    try:
        raw = input(f"{INPUT_PREFIX}{prompt}").strip()
    except KeyboardInterrupt:
        _print_goodbye()
        raise SystemExit(0)
    print("")
    return raw


def _prompt_decrypt_action() -> str:
    try:
        raw = input(
            f"{INPUT_PREFIX}Enter=try another key, c=copy+menu, q=menu: "
        ).strip().lower()
    except KeyboardInterrupt:
        _print_goodbye()
        raise SystemExit(0)
    return raw


def _print_help_sections(sections: List[List[str]]) -> None:
    if not sys.stdin.isatty():
        for section in sections:
            for line in section:
                print(line)
            print("")
        return
    show_all = False
    for section in sections:
        for line in section:
            print(line)
        print("")
        if show_all:
            continue
        action = _prompt_page_action()
        if action in {"a", "all"}:
            show_all = True
        elif action in {"q", "quit"}:
            return


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _format_cap(value: int, zero_label: str) -> str:
    if value <= 0:
        return zero_label
    return str(value)


@dataclass(frozen=True)
class DecodedItem:
    chain: Tuple[str, ...]
    data: bytes


@dataclass(frozen=True)
class ScoredItem:
    item: DecodedItem
    output_text: str
    abs_score: float
    delta: float


@dataclass(frozen=True)
class DecodeSummary:
    printed: int
    total_candidates: int
    total_filtered: int
    aborted: bool = False


def _label(result: DecodeResult) -> str:
    if result.note:
        return f"{result.name}:{result.note}"
    return result.name


def _gather(
    text: str,
    data: bytes,
    decoders: Sequence[Decoder],
    depth: int,
    max_results: int,
) -> List[DecodedItem]:
    results: List[DecodedItem] = []
    seen = set()
    queue = [(text, data, tuple())]
    for level in range(depth):
        next_queue = []
        for cur_text, cur_data, chain in queue:
            for decoder in decoders:
                for res in decoder.func(cur_text, cur_data):
                    new_chain = chain + (_label(res),)
                    results.append(DecodedItem(new_chain, res.output))
                    if len(results) >= max_results:
                        return results
                    digest = hashlib.sha256(res.output).digest()
                    if digest in seen:
                        continue
                    seen.add(digest)
                    if level + 1 < depth:
                        next_queue.append((to_text(res.output), res.output, new_chain))
        queue = next_queue
    return results


def _rank_key(abs_score: float, delta: float, mode: str) -> tuple:
    if mode == "absolute":
        return (abs_score, delta)
    if mode == "delta":
        return (delta, abs_score)
    combined = abs_score + max(0.0, delta)
    return (combined, abs_score, delta)


def _base_name(chain: Tuple[str, ...]) -> str:
    if not chain:
        return ""
    last = chain[-1]
    return last.split(":", 1)[0]


def _prompt_choice(prompt: str, options: List[str], default: str) -> str:
    while True:
        raw = _prompt_line(prompt).lower()
        if not raw:
            return default
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        if raw in options:
            return raw
        print(f"Invalid choice. Options: {', '.join(options)}")


def _prompt_int(
    prompt: str, min_value: int, max_value: int, default: Optional[int] = None
) -> int:
    while True:
        raw = _prompt_line(prompt)
        if not raw:
            if default is not None:
                return default
            print(f"Enter a number between {min_value} and {max_value}.")
            continue
        try:
            value = int(raw)
        except ValueError:
            print("Enter a valid integer.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"Value must be between {min_value} and {max_value}.")


def _prompt_float(
    prompt: str, min_value: float, max_value: float, default: Optional[float] = None
) -> float:
    while True:
        raw = _prompt_line(prompt)
        if not raw:
            if default is not None:
                return default
            print(f"Enter a number between {min_value} and {max_value}.")
            continue
        try:
            value = float(raw)
        except ValueError:
            print("Enter a valid number.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"Value must be between {min_value} and {max_value}.")


def _prompt_bool(prompt: str, default: bool) -> bool:
    options = "Y/n" if default else "y/N"
    while True:
        raw = _prompt_line(f"{prompt} [{options}]: ").lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Enter y or n.")


def _prompt_text() -> str:
    print("")
    print("Enter or paste input.")
    print("Finish with an empty line (press Enter on a blank line).")
    lines = []
    while True:
        try:
            line = input(INPUT_PREFIX)
        except EOFError:
            break
        except KeyboardInterrupt:
            _print_goodbye()
            raise SystemExit(0)
        if line == "":
            break
        lines.append(line)
    print("")
    return "\n".join(lines)


def _pause(message: str = "Press Enter to return to the menu.") -> None:
    try:
        input(f"{INPUT_PREFIX}{message}")
    except KeyboardInterrupt:
        _print_goodbye()
        raise SystemExit(0)


def _prompt_page_action() -> str:
    prompt = f"{INPUT_PREFIX}Enter=next, a=all results, q=menu: "
    try:
        raw = input(prompt).strip().lower()
    except KeyboardInterrupt:
        _print_goodbye()
        raise SystemExit(0)
    if not raw:
        print("")
    return raw


def _print_goodbye() -> None:
    print("")
    print("Goodbye.")
    print("")


@contextmanager
def _suppress_ctrl_echo() -> None:
    if termios is None or not sys.stdin.isatty() or not hasattr(termios, "ECHOCTL"):
        yield
        return
    fd = sys.stdin.fileno()
    try:
        attrs = termios.tcgetattr(fd)
    except termios.error:
        yield
        return
    new_attrs = list(attrs)
    new_attrs[3] = new_attrs[3] & ~termios.ECHOCTL
    try:
        termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, attrs)


def _copy_to_clipboard(text: str) -> bool:
    if not text:
        return False
    commands = []
    if sys.platform == "darwin" and shutil.which("pbcopy"):
        commands.append(["pbcopy"])
    if shutil.which("wl-copy"):
        commands.append(["wl-copy"])
    if shutil.which("xclip"):
        commands.append(["xclip", "-selection", "clipboard"])
    if shutil.which("clip"):
        commands.append(["clip"])
    for cmd in commands:
        try:
            subprocess.run(cmd, input=text, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        return True
    return False


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def _set_color_mode(mode: str) -> None:
    global COLOR_ENABLED
    if mode == "always":
        COLOR_ENABLED = True
    elif mode == "never":
        COLOR_ENABLED = False
    else:
        COLOR_ENABLED = _supports_color()


def _print_interactive_help() -> None:
    _print_section("Help and reference")
    sections: List[List[str]] = []
    sections.append(
        [
            "How it works:",
            "- Choose decode/decrypt or encode/encrypt from the menu.",
            "- Paste any text directly; no shell quoting needed.",
            "- End input with an empty line.",
            "- For advanced settings, choose the prompt options when asked.",
        ]
    )
    sections.append(
        [
            "Definitions:",
            "- Encoding/Decoding: non-keyed transforms (formats and simple ciphers).",
            "- Encrypting/Decrypting: keyed ciphers that require a secret key.",
        ]
    )
    sections.append(
        [
            "Learn (cipher glossary):",
            "- Browse or search all 33 ciphers and encodings.",
            "- View detailed explanations, historical context, and references.",
            "- Learn how each cipher works and when it was used.",
            "- Access from main menu option 5 or use: svelo --info <cipher>",
        ]
    )
    decode_section = ["Decode (non-keyed):"]
    for decoder in _select_decoders(get_decoders(), _DECODE_METHODS):
        decode_section.append(f"- {decoder.name}: {decoder.description}")
    sections.append(decode_section)
    decrypt_section = ["Decrypt (keyed ciphers):"]
    for name, description in _KEYED_CIPHERS.items():
        decrypt_section.append(f"- {name}: {description}")
    sections.append(decrypt_section)
    encode_section = ["Encode (non-keyed):"]
    for encoder in _select_encoders(get_encoders(), _ENCODE_METHODS):
        encode_section.append(f"- {encoder.name}: {encoder.description}")
    sections.append(encode_section)
    encrypt_section = ["Encrypt (keyed ciphers):"]
    for encoder in _select_encoders(get_encoders(), _ENCRYPT_METHODS):
        encrypt_section.append(f"- {encoder.name}: {encoder.description}")
    sections.append(encrypt_section)
    sections.append(
        [
            "Notes:",
            "- Decrypt/Encrypt modes are for keyed ciphers only.",
            "- You can retry keys until you find a readable result.",
            "- Encoded or encrypted output can be copied to the clipboard.",
            "- This tool is provided \"as is\" without warranty.",
            "- Do not rely on it for security-critical or irreversible data.",
            "- Report issues: https://github.com/MSNYC/Svelo/issues",
        ]
    )
    _print_help_sections(sections)


def _print_main_menu() -> None:
    _clear_view()
    _print_section("Svelo: Classic Ciphers & Encodings")
    print("Main menu")
    print("")
    print("1) Decode (non-keyed)")
    print("2) Decrypt (keyed)")
    print("3) Encode (non-keyed)")
    print("4) Encrypt (keyed)")
    print("5) Learn (cipher glossary)")
    print("6) Help and reference")
    print("7) Quit")


def _select_encoder(
    encoders: Sequence[Encoder],
    name: Optional[str],
    prompt_label: str = "encoder",
) -> Encoder:
    by_name = {encoder.name: encoder for encoder in encoders}
    if name:
        encoder = by_name.get(name)
        if encoder is None:
            raise SystemExit(f"Unknown encoder: {name}")
        return encoder
    options = [encoder.name for encoder in encoders]
    print(f"Select {prompt_label}:")
    for idx, encoder in enumerate(encoders, start=1):
        print(f"{idx}. {encoder.name} - {encoder.description}")
    choice = _prompt_choice("Enter number or name: ", options, options[0])
    return by_name[choice]


def _encode_with_params(
    encoder: Encoder,
    text: str,
    echo: Optional[Callable[[str], None]] = None,
    railfence_strip_spaces: Optional[bool] = None,
    key: Optional[str] = None,
    key2: Optional[str] = None,
) -> str:
    name = encoder.name
    if name == "caesar":
        shift = _prompt_int("Shift (1-25): ", 1, 25)
        if echo:
            echo(f"Shift: {shift}")
        return encode_caesar(text, shift)
    if name == "fibonacci":
        seed = _prompt_choice(
            "Seed [0,1 or 1,1] (default 0,1): ", ["0,1", "1,1"], "0,1"
        )
        advance = _prompt_choice(
            "Advance on [alpha/all] (default alpha): ", ["alpha", "all"], "alpha"
        )
        if echo:
            echo(f"Seed: {seed}")
            echo(f"Advance on: {advance}")
        seed_a, seed_b = (int(part) for part in seed.split(","))
        return encode_fibonacci(text, seed_a, seed_b, advance == "all")
    if name == "bacon":
        variant = _prompt_choice(
            "Bacon variant [classic/binary] (default classic): ",
            ["classic", "binary"],
            "classic",
        )
        if echo:
            echo(f"Variant: {variant}")
        return encode_bacon(text, variant)
    if name == "polybius":
        return encode_polybius(text)
    if name == "morse":
        return encode_morse(text)
    if name == "railfence":
        rails = _prompt_int("Rails (2-6): ", 2, 6)
        if railfence_strip_spaces is None:
            strip_spaces = _prompt_bool("Strip spaces", False)
        else:
            strip_spaces = railfence_strip_spaces
        if echo:
            echo(f"Rails: {rails}")
            echo(f"Strip spaces: {_format_bool(strip_spaces)}")
        return encode_railfence(text, rails, strip_spaces)
    if name == "vigenere":
        cipher_key = key or _prompt_line("Vigenere key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_vigenere(text, cipher_key)
    if name == "beaufort":
        cipher_key = key or _prompt_line("Beaufort key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_beaufort(text, cipher_key)
    if name == "variant":
        cipher_key = key or _prompt_line("Variant Beaufort key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_variant(text, cipher_key)
    if name == "autokey":
        cipher_key = key or _prompt_line("Autokey key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_autokey(text, cipher_key)
    if name == "keyword":
        cipher_key = key or _prompt_line("Keyword (substitution): ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_keyword_substitution(text, cipher_key)
    if name == "columnar":
        cipher_key = key or _prompt_line("Columnar key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_columnar(text, cipher_key)
    if name == "playfair":
        cipher_key = key or _prompt_line("Playfair key: ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_playfair(text, cipher_key)
    if name == "hill":
        cipher_key = key or _prompt_line("Hill key (4 letters): ")
        if echo:
            echo(f"Key: {cipher_key}")
        return encode_hill(text, cipher_key)
    if name == "adfgx":
        square_key = key or _prompt_line("ADFGX square key: ")
        transposition_key = key2 or _prompt_line("ADFGX transposition key: ")
        if echo:
            echo(f"Square key: {square_key}")
            echo(f"Transposition key: {transposition_key}")
        return encode_adfgx(text, square_key, transposition_key)
    if name == "adfgvx":
        square_key = key or _prompt_line("ADFGVX square key: ")
        transposition_key = key2 or _prompt_line("ADFGVX transposition key: ")
        if echo:
            echo(f"Square key: {square_key}")
            echo(f"Transposition key: {transposition_key}")
        return encode_adfgvx(text, square_key, transposition_key)
    if name == "scytale":
        cols = _prompt_int("Columns (2-6): ", 2, 6)
        if echo:
            echo(f"Columns: {cols}")
        return encode_scytale(text, cols)
    if encoder.func is None:
        raise SystemExit(f"Encoder requires parameters: {name}")
    return encoder.func(text)


def _format_output(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


def _format_preview(text: str, max_chars: int = 120) -> str:
    compact = text.replace("\n", "\\n")
    if not compact:
        return "(empty)"
    return _format_output(compact, max_chars)


def _line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def _print_results(
    items: Iterable[ScoredItem],
    show_hex: bool,
    max_chars: int,
    page_size: int,
    show_metrics: bool,
) -> Tuple[int, bool]:
    printed = 0
    aborted = False
    paging = page_size > 0 and sys.stdin.isatty()
    page_count = 0
    for scored in items:
        if show_metrics:
            chain = " -> ".join(scored.item.chain)
            print(
                f"[{chain}] abs={scored.abs_score:.2f} delta={scored.delta:+.2f} len={len(scored.item.data)}"
            )
        else:
            chain = " -> ".join(scored.item.chain)
            print(f"[{chain}]")
        print(_format_output(scored.output_text, max_chars))
        if show_hex:
            print(scored.item.data.hex())
        if "I/J" in scored.output_text or "U/V" in scored.output_text:
            print("Note: I/J and U/V mark ambiguous letters in this cipher.")
        print("")
        printed += 1
        if paging:
            page_count += 1
            if page_count >= page_size:
                action = _prompt_page_action()
                if action in {"a", "all"}:
                    paging = False
                elif action in {"q", "quit"}:
                    aborted = True
                    break
                page_count = 0
        if aborted:
            break
    return printed, aborted


def _select_decoders(all_decoders: Sequence[Decoder], names: Sequence[str]) -> List[Decoder]:
    if not names:
        return list(all_decoders)
    by_name = {decoder.name: decoder for decoder in all_decoders}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise SystemExit(f"Unknown decoder(s): {', '.join(missing)}")
    return [by_name[name] for name in names]


def _select_encoders(all_encoders: Sequence[Encoder], names: Sequence[str]) -> List[Encoder]:
    if not names:
        return list(all_encoders)
    by_name = {encoder.name: encoder for encoder in all_encoders}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise SystemExit(f"Unknown encoder(s): {', '.join(missing)}")
    return [by_name[name] for name in names]


def _read_input(arg_value: Optional[str], paste: bool) -> str:
    if paste and arg_value is not None:
        raise SystemExit("Use --paste without an inline input argument.")
    if arg_value is not None and not paste:
        return arg_value
    if paste:
        if sys.stdin.isatty():
            print(
                "Paste input now, then press Ctrl-D (EOF) to finish.",
                file=sys.stderr,
            )
        data = sys.stdin.read()
        if not data:
            raise SystemExit("No input provided.")
        return data
    if sys.stdin.isatty():
        raise SystemExit(
            "No input provided. If your shell shows a prompt like dquote> or "
            "bquote>, you have an unclosed quote/backtick. Use --paste or pipe "
            "input via stdin."
        )
    return sys.stdin.read()


def _decode_text(
    text: str,
    decoders: Sequence[Decoder],
    decoder_names: Sequence[str],
    chain_depth: int,
    min_score: float,
    min_delta: float,
    show_all: bool,
    top: int,
    rank: str,
    max_per_decoder: int,
    max_results: int,
    show_hex: bool,
    max_chars: int,
    page_size: int,
    show_metrics: bool,
) -> DecodeSummary:
    data = text.encode("utf-8")
    active = _select_decoders(decoders, decoder_names)
    results = _gather(text, data, active, chain_depth, max_results)

    deduped = []
    seen = set()
    for item in results:
        key = (item.chain, item.data)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    input_score = english_score(text.strip())
    scored_items: List[ScoredItem] = []
    for item in deduped:
        output_text = to_text(item.data)
        abs_score = english_score(output_text.strip())
        delta = abs_score - input_score
        scored_items.append(ScoredItem(item, output_text, abs_score, delta))

    scored_items.sort(
        key=lambda scored: _rank_key(scored.abs_score, scored.delta, rank),
        reverse=True,
    )

    total_candidates = len(scored_items)
    if show_all:
        filtered = scored_items
        total_filtered = total_candidates
    else:
        filtered = [
            scored
            for scored in scored_items
            if scored.abs_score >= min_score and scored.delta >= min_delta
        ]
        if max_per_decoder > 0:
            capped = []
            counts = {}
            for scored in filtered:
                base = _base_name(scored.item.chain)
                if counts.get(base, 0) >= max_per_decoder:
                    continue
                counts[base] = counts.get(base, 0) + 1
                capped.append(scored)
            filtered = capped
        total_filtered = len(filtered)
        filtered = filtered[:top]

    printed, aborted = _print_results(
        filtered, show_hex, max_chars, page_size, show_metrics
    )
    if printed == 0:
        raise SystemExit("No results matched the current filters.")
    return DecodeSummary(
        printed=printed,
        total_candidates=total_candidates,
        total_filtered=total_filtered,
        aborted=aborted,
    )


def _decrypt_with_key_loop(cipher: str, text: str) -> bool:
    while True:
        try:
            if cipher == "vigenere":
                key = _prompt_line("Vigenere key: ")
                output = vigenere_decrypt(text, key)
            elif cipher == "beaufort":
                key = _prompt_line("Beaufort key: ")
                output = beaufort_decrypt(text, key)
            elif cipher == "variant":
                key = _prompt_line("Variant Beaufort key: ")
                output = variant_beaufort_decrypt(text, key)
            elif cipher == "autokey":
                key = _prompt_line("Autokey key: ")
                output = autokey_decrypt(text, key)
            elif cipher == "keyword":
                key = _prompt_line("Keyword (substitution): ")
                output = keyword_substitution_decrypt(text, key)
            elif cipher == "columnar":
                key = _prompt_line("Columnar key: ")
                output = columnar_decrypt(text, key)
            elif cipher == "playfair":
                key = _prompt_line("Playfair key: ")
                output = playfair_decrypt(text, key)
            elif cipher == "hill":
                key = _prompt_line("Hill key (4 letters): ")
                output = hill_decrypt(text, key)
            elif cipher == "adfgx":
                square_key = _prompt_line("ADFGX square key: ")
                transposition_key = _prompt_line("ADFGX transposition key: ")
                output = adfgx_decrypt(text, square_key, transposition_key)
            elif cipher == "adfgvx":
                square_key = _prompt_line("ADFGVX square key: ")
                transposition_key = _prompt_line("ADFGVX transposition key: ")
                output = adfgvx_decrypt(text, square_key, transposition_key)
            else:
                raise ValueError(f"Unknown cipher: {cipher}")
        except ValueError as exc:
            print(str(exc))
            continue

        _print_section("Decrypted output")
        print(output)
        action = _prompt_decrypt_action()
        if action in {"c", "copy", "y", "yes"}:
            if _copy_to_clipboard(output):
                print("Copied to clipboard.")
            return True
        if action in {"q", "quit"}:
            return False
        continue


def _learn_menu() -> None:
    """Interactive glossary and learning menu."""
    while True:
        _clear_view()
        _print_section("Learn: Cipher Glossary")
        print("Learn about the ciphers and encodings in Svelo")
        print("")
        print("1) Browse all ciphers")
        print("2) Search for a cipher")
        print("3) Back to main menu")
        print("")

        choice = _prompt_line("Select an option: ").lower()

        if choice in {"3", "back", "menu", "q", "quit"}:
            return

        if choice in {"1", "browse"}:
            _clear_view()
            _print_section("Learn: All Ciphers")
            entries = get_all_entries()
            print(f"Showing {len(entries)} cipher(s) and encoding(s):\n")
            for i, entry in enumerate(entries, 1):
                print(f"{i}) {entry.name} - {entry.description[:70]}...")
            print("")
            print("Enter a number or cipher name to learn more, or press Enter to continue.")
            selection = _prompt_line("Selection: ")
            if selection:
                # Try as number first
                entry = None
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(entries):
                        entry = entries[idx]
                except ValueError:
                    # Not a number, try as cipher name
                    entry = get_entry(selection)

                if entry:
                    _clear_view()
                    print(format_entry(entry))
                    print("")
                    _pause()
                else:
                    print(f"No entry found for '{selection}'")
                    _pause()

        elif choice in {"2", "search"}:
            query = _prompt_line("Search (name, category, or keyword): ")
            if not query:
                continue
            results = search_entries(query)
            if not results:
                print(f"No results found for '{query}'")
                _pause()
                continue

            _clear_view()
            _print_section(f"Learn: Search Results for '{query}'")
            print(f"Found {len(results)} result(s):\n")
            for i, entry in enumerate(results, 1):
                print(f"{i}) {entry.name} - {entry.description[:70]}...")
            print("")
            print("Enter a number or cipher name to learn more, or press Enter to continue.")
            selection = _prompt_line("Selection: ")
            if selection:
                # Try as number first
                entry = None
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(results):
                        entry = results[idx]
                except ValueError:
                    # Not a number, try as cipher name
                    entry = get_entry(selection)

                if entry:
                    _clear_view()
                    print(format_entry(entry))
                    print("")
                    _pause()
                else:
                    print(f"No entry found for '{selection}'")
                    _pause()

        else:
            # Try treating input as a direct cipher name
            entry = get_entry(choice)
            if entry:
                _clear_view()
                print(format_entry(entry))
                print("")
                _pause()
            else:
                print("Unknown option. Enter 1-3 or a cipher name.")
                _pause()


def _interactive_loop(decoders: Sequence[Decoder], encoders: Sequence[Encoder]) -> None:
    _clear_view()
    _print_section("Svelo: Classic Ciphers & Encodings")
    print("Guided decode and encode with step-by-step summaries.")
    while True:
        _print_main_menu()
        choice = _prompt_line("Select an option: ").lower()
        if choice in {"7", "quit"}:
            return
        if choice in {"6", "help", "reference"}:
            _print_interactive_help()
            _pause()
            continue
        if choice in {"5", "learn", "glossary"}:
            _learn_menu()
            continue
        if choice in {"1", "decode"}:
            _print_section("Decode: Step 1/3 - Input")
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            print("")
            print("Input summary:")
            print(f"Preview: {_format_preview(text)}")
            print(f"Characters: {len(text)}")
            print(f"Lines: {_line_count(text)}")

            _print_section("Decode: Step 2/3 - Decoder selection")
            active_decoders = _select_decoders(decoders, _DECODE_METHODS)
            run_all = _prompt_bool("Run all decoders", True)
            if run_all:
                decoder_names = []
                decoder_summary = f"all ({len(active_decoders)} available)"
            else:
                options = [decoder.name for decoder in active_decoders]
                print("")
                print("Select a decoder:")
                for idx, decoder in enumerate(active_decoders, start=1):
                    print(f"{idx}. {decoder.name} - {decoder.description}")
                choice = _prompt_choice("Enter number or name: ", options, options[0])
                decoder_names = [choice]
                decoder_summary = choice
            print("")
            print("Selection:")
            print(f"Decoders: {decoder_summary}")

            _print_section("Decode: Step 3/3 - Settings")
            advanced = not _prompt_bool("Skip advanced settings? (recommended)", True)
            chain_depth = DEFAULT_CHAIN_DEPTH
            min_score = DEFAULT_MIN_SCORE
            min_delta = DEFAULT_MIN_DELTA
            show_all = bool(decoder_names)
            top = DEFAULT_TOP
            rank = DEFAULT_RANK
            max_per_decoder = DEFAULT_MAX_PER_DECODER
            max_results = DEFAULT_MAX_RESULTS
            show_hex = DEFAULT_SHOW_HEX
            max_chars = DEFAULT_MAX_CHARS
            page_size = DEFAULT_PAGE_SIZE
            show_metrics = False
            if not decoder_names and not show_all:
                top = DEFAULT_MAX_RESULTS
                max_per_decoder = 0
            if advanced:
                show_metrics = True
                chain_depth = _prompt_int(
                    f"Chain depth [{DEFAULT_CHAIN_DEPTH}]: ",
                    1,
                    10,
                    DEFAULT_CHAIN_DEPTH,
                )
                min_score = _prompt_float(
                    f"Min score [{DEFAULT_MIN_SCORE}]: ", 0.0, 1.0, DEFAULT_MIN_SCORE
                )
                min_delta = _prompt_float(
                    f"Min delta [{DEFAULT_MIN_DELTA}]: ", -1.0, 1.0, DEFAULT_MIN_DELTA
                )
                show_all = _prompt_bool("Show all results", show_all)
                top = _prompt_int(
                    f"Top results [{top}]: ", 1, 50, top
                )
                rank = _prompt_choice(
                    f"Rank mode [{DEFAULT_RANK}]: ",
                    ["absolute", "delta", "both"],
                    DEFAULT_RANK,
                )
                max_per_decoder = _prompt_int(
                    f"Max per decoder [{max_per_decoder}]: ",
                    0,
                    10,
                    max_per_decoder,
                )
                max_results = _prompt_int(
                    f"Max results [{DEFAULT_MAX_RESULTS}]: ",
                    1,
                    500,
                    DEFAULT_MAX_RESULTS,
                )
                show_hex = _prompt_bool("Show hex output", False)
                max_chars = _prompt_int(
                    f"Max chars [{DEFAULT_MAX_CHARS}]: ",
                    0,
                    10000,
                    DEFAULT_MAX_CHARS,
                )
                page_size = _prompt_int(
                    f"Results per page [{page_size}]: ",
                    0,
                    50,
                    page_size,
                )
            print("")
            print("Settings summary:")
            print(f"Advanced settings: {_format_bool(advanced)}")
            print(f"Chain depth: {chain_depth}")
            print(f"Min score: {min_score:.2f}")
            print(f"Min delta: {min_delta:+.2f}")
            print(f"Show all results: {_format_bool(show_all)}")
            print(f"Top results: {top}")
            print(f"Rank mode: {rank}")
            print(f"Max per decoder: {_format_cap(max_per_decoder, 'no cap')}")
            print(f"Max results: {max_results}")
            print(f"Show hex output: {_format_bool(show_hex)}")
            print(f"Max chars: {_format_cap(max_chars, 'no limit')}")
            print(f"Results per page: {_format_cap(page_size, 'all at once')}")
            print(f"Show metrics: {_format_bool(show_metrics)}")

            _print_section("Decode: Running")
            print("Decoding...")
            try:
                summary = _decode_text(
                    text,
                    active_decoders,
                    decoder_names,
                    chain_depth,
                    min_score,
                    min_delta,
                    show_all,
                    top,
                    rank,
                    max_per_decoder,
                    max_results,
                    show_hex,
                    max_chars,
                    page_size,
                    show_metrics,
                )
            except SystemExit as exc:
                print(str(exc))
                print("")
                continue
            if summary.aborted:
                print("")
                continue
            print("")
            print(
                f"Done. {summary.printed} of {summary.total_candidates} result(s) shown."
            )
            if not show_all and summary.printed < summary.total_candidates:
                show_more = _prompt_bool(
                    "Show all results (including low-score candidates)", False
                )
                if show_more:
                    _print_section("Decode: All results")
                    try:
                        summary = _decode_text(
                            text,
                            active_decoders,
                            decoder_names,
                            chain_depth,
                            min_score,
                            min_delta,
                            True,
                            top,
                            rank,
                            max_per_decoder,
                            max_results,
                            show_hex,
                            max_chars,
                            page_size,
                            show_metrics,
                        )
                    except SystemExit as exc:
                        print(str(exc))
                        print("")
                        continue
                    if summary.aborted:
                        print("")
                        continue
                    print("")
                    print(
                        f"Done. {summary.printed} of {summary.total_candidates} result(s) shown."
                    )
            if _prompt_bool("Return to main menu", True):
                continue
            return
        if choice in {"2", "decrypt"}:
            _print_section("Decrypt: Step 1/3 - Input")
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            print("")
            print("Input summary:")
            print(f"Preview: {_format_preview(text)}")
            print(f"Characters: {len(text)}")
            print(f"Lines: {_line_count(text)}")

            _print_section("Decrypt: Step 2/3 - Decryption method selection")
            options = list(_KEYED_CIPHERS.keys())
            print("")
            print("Select a cipher:")
            for idx, name in enumerate(options, start=1):
                print(f"{idx}. {name} - {_KEYED_CIPHERS[name]}")
            choice = _prompt_choice("Enter number or name: ", options, options[0])
            decoder_names = [choice]
            decoder_summary = choice
            print("")
            print("Selection:")
            print(f"Ciphers: {decoder_summary}")

            _decrypt_with_key_loop(decoder_names[0], text)
            continue
        if choice in {"3", "encode"}:
            _print_section("Encode: Step 1/3 - Input")
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            print("")
            print("Input summary:")
            print(f"Preview: {_format_preview(text)}")
            print(f"Characters: {len(text)}")
            print(f"Lines: {_line_count(text)}")

            _print_section("Encode: Step 2/3 - Encoding selection")
            active_encoders = _select_encoders(encoders, _ENCODE_METHODS)
            encoder = _select_encoder(active_encoders, None, "encoding method")
            print("")
            print("Selection:")
            print(f"Encoding: {encoder.name} - {encoder.description}")
            try:
                _print_section("Encode: Step 3/3 - Encoding settings")
                settings: List[str] = []

                def _record_setting(line: str) -> None:
                    settings.append(line)

                output = _encode_with_params(encoder, text, _record_setting)
            except ValueError as exc:
                print(str(exc))
                continue
            print("")
            print("Settings summary:")
            if settings:
                for line in settings:
                    print(line)
            else:
                print("No additional settings.")
            _print_section("Encoded output")
            print(output)
            if _copy_to_clipboard(output):
                print("")
                print("Copied to clipboard.")
            if _prompt_bool("Return to main menu", True):
                continue
            return
        if choice in {"4", "encrypt"}:
            _print_section("Encrypt: Step 1/3 - Input")
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            print("")
            print("Input summary:")
            print(f"Preview: {_format_preview(text)}")
            print(f"Characters: {len(text)}")
            print(f"Lines: {_line_count(text)}")

            _print_section("Encrypt: Step 2/3 - Encryption selection")
            active_encoders = _select_encoders(encoders, _ENCRYPT_METHODS)
            encoder = _select_encoder(active_encoders, None, "encryption method")
            print("")
            print("Selection:")
            print(f"Encryption: {encoder.name} - {encoder.description}")
            try:
                _print_section("Encrypt: Step 3/3 - Encryption settings")
                settings: List[str] = []

                def _record_setting(line: str) -> None:
                    settings.append(line)

                output = _encode_with_params(encoder, text, _record_setting)
            except ValueError as exc:
                print(str(exc))
                continue
            print("")
            print("Settings summary:")
            if settings:
                for line in settings:
                    print(line)
            else:
                print("No additional settings.")
            _print_section("Encrypted output")
            print(output)
            if _copy_to_clipboard(output):
                print("")
                print("Copied to clipboard.")
            if _prompt_bool("Return to main menu", True):
                continue
            return
        print("Unknown option. Enter 1-6 or type a menu name.")


def main() -> None:
    try:
        with _suppress_ctrl_echo():
            parser = argparse.ArgumentParser(
                prog="svelo",
                description="Try common decoders against an input string",
            )
            parser.add_argument("input", nargs="?", help="input string (or use stdin)")
            parser.add_argument(
                "--paste",
                action="store_true",
                help="read input from stdin (safe for quotes/backticks)",
            )
            mode = parser.add_mutually_exclusive_group()
            mode.add_argument("--encode", action="store_true", help="encode input")
            mode.add_argument(
                "--decode", action="store_true", help="decode input (default)"
            )
            mode.add_argument(
                "--interactive", action="store_true", help="interactive menu"
            )
            parser.add_argument(
                "--list", action="store_true", help="list available decoders"
            )
            parser.add_argument(
                "--list-encoders", action="store_true", help="list available encoders"
            )
            parser.add_argument(
                "--info", metavar="CIPHER", help="show glossary entry for a cipher"
            )
            parser.add_argument(
                "--encoder", help="encoder to use in encode mode (skips prompt)"
            )
            parser.add_argument(
                "--decoder",
                action="append",
                default=[],
                help="run only specific decoders (repeatable)",
            )
            parser.add_argument(
                "--chain-depth",
                type=int,
                default=DEFAULT_CHAIN_DEPTH,
                help="number of decode passes to attempt",
            )
            parser.add_argument(
                "--min-score",
                type=float,
                default=DEFAULT_MIN_SCORE,
                help="minimum absolute score (0-1)",
            )
            parser.add_argument(
                "--min-delta",
                type=float,
                default=DEFAULT_MIN_DELTA,
                help="minimum score improvement vs input (-1 to 1)",
            )
            parser.add_argument("--all", action="store_true", help="show all results")
            parser.add_argument(
                "--top",
                type=int,
                default=DEFAULT_TOP,
                help="show only the top N ranked results",
            )
            parser.add_argument(
                "--rank",
                choices=["absolute", "delta", "both"],
                default=DEFAULT_RANK,
                help="ranking mode for results",
            )
            parser.add_argument(
                "--max-per-decoder",
                type=int,
                default=DEFAULT_MAX_PER_DECODER,
                help="cap results per decoder family (0 = no cap)",
            )
            parser.add_argument(
                "--max-results",
                type=int,
                default=DEFAULT_MAX_RESULTS,
                help="stop after N results",
            )
            parser.add_argument(
                "--show-hex",
                action="store_true",
                help="include hex output for each result",
            )
            parser.add_argument(
                "--max-chars",
                type=int,
                default=DEFAULT_MAX_CHARS,
                help="truncate long outputs at N characters (0 = no limit)",
            )
            parser.add_argument(
                "--color",
                choices=["auto", "always", "never"],
                default="auto",
                help="color output: auto, always, or never",
            )
            parser.add_argument(
                "--railfence-strip-spaces",
                action="store_true",
                help="strip spaces before rail fence encoding",
            )
            parser.add_argument(
                "--key",
                help="key for keyed ciphers (encrypt mode)",
            )
            parser.add_argument(
                "--key2",
                help="second key for keyed ciphers (adfgx/adfgvx encrypt mode)",
            )

            args = parser.parse_args()
            decoders = get_decoders()
            encoders = get_encoders()
            _set_color_mode(args.color)

            if args.list:
                for decoder in decoders:
                    print(f"{decoder.name}: {decoder.description}")
                return
            if args.list_encoders:
                for encoder in encoders:
                    print(f"{encoder.name}: {encoder.description}")
                return
            if args.info:
                entry = get_entry(args.info)
                if entry:
                    print(format_entry(entry))
                else:
                    print(f"No glossary entry found for '{args.info}'")
                    print("\nAvailable ciphers:")
                    for e in get_all_entries():
                        print(f"  - {e.name.lower()}")
                return

            if args.encode and args.decoder:
                raise SystemExit(
                    "Use --encoder with --encode (decoders are for decode mode)."
                )

            if args.interactive and args.input is not None:
                raise SystemExit("Do not pass input with --interactive.")

            if args.chain_depth < 1:
                raise SystemExit("--chain-depth must be >= 1")
            if args.max_results < 1:
                raise SystemExit("--max-results must be >= 1")
            if args.top < 1:
                raise SystemExit("--top must be >= 1")
            if args.max_per_decoder < 0:
                raise SystemExit("--max-per-decoder must be >= 0")

            if args.interactive or (
                args.input is None
                and sys.stdin.isatty()
                and not args.list
                and not args.list_encoders
                and not args.encode
                and not args.decode
            ):
                _interactive_loop(decoders, encoders)
                return

            if (
                (args.encode or args.decode)
                and args.input is None
                and sys.stdin.isatty()
                and not args.paste
            ):
                text = _prompt_text()
            else:
                text = _read_input(args.input, args.paste)

            if args.encode:
                if not text:
                    raise SystemExit("No input provided.")
                if args.encoder is None and not sys.stdin.isatty():
                    raise SystemExit(
                        "Encode mode requires --encoder when input is piped."
                    )
                encoder = _select_encoder(encoders, args.encoder)
                if encoder.name in _ENCRYPT_METHODS and not sys.stdin.isatty():
                    if args.key is None:
                        raise SystemExit(
                            "Keyed encrypt requires --key when input is piped."
                        )
                    if encoder.name in {"adfgx", "adfgvx"} and args.key2 is None:
                        raise SystemExit(
                            "ADFGX/ADFGVX encrypt requires --key2 when input is piped."
                        )
                try:
                    output = _encode_with_params(
                        encoder,
                        text,
                        railfence_strip_spaces=args.railfence_strip_spaces,
                        key=args.key,
                        key2=args.key2,
                    )
                except ValueError as exc:
                    raise SystemExit(str(exc)) from exc
                print(output)
                if _copy_to_clipboard(output):
                    print("Copied to clipboard.")
                return

            show_all = args.all
            top = args.top
            max_per_decoder = args.max_per_decoder
            if (
                args.decoder
                and not args.all
                and args.top == DEFAULT_TOP
                and args.max_per_decoder == DEFAULT_MAX_PER_DECODER
            ):
                show_all = True
            if (
                not args.decoder
                and not args.all
                and args.top == DEFAULT_TOP
                and args.max_per_decoder == DEFAULT_MAX_PER_DECODER
            ):
                top = DEFAULT_MAX_RESULTS
                max_per_decoder = 0

            _decode_text(
                text,
                decoders,
                args.decoder,
                args.chain_depth,
                args.min_score,
                args.min_delta,
                show_all,
                top,
                args.rank,
                max_per_decoder,
                args.max_results,
                args.show_hex,
                args.max_chars,
                0,
                True,
            )
    except KeyboardInterrupt:
        _print_goodbye()
        raise SystemExit(0)


if __name__ == "__main__":
    main()
