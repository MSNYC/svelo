import argparse
import hashlib
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from .decoders import (
    DecodeResult,
    Decoder,
    Encoder,
    encode_bacon,
    encode_caesar,
    encode_fibonacci,
    encode_morse,
    encode_polybius,
    encode_railfence,
    encode_scytale,
    get_decoders,
    get_encoders,
)
from .utils import english_score, to_text

DEFAULT_CHAIN_DEPTH = 1
DEFAULT_MIN_SCORE = 0.25
DEFAULT_MIN_DELTA = 0.0
DEFAULT_TOP = 5
DEFAULT_RANK = "both"
DEFAULT_MAX_PER_DECODER = 1
DEFAULT_MAX_RESULTS = 50
DEFAULT_SHOW_HEX = False
DEFAULT_MAX_CHARS = 2000


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
        raw = input(prompt).strip().lower()
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
        raw = input(prompt).strip()
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
        raw = input(prompt).strip()
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
        raw = input(f"{prompt} [{options}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Enter y or n.")


def _prompt_text() -> str:
    print("Enter or paste input. Finish with an empty line.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def _print_interactive_help() -> None:
    print("Interactive mode:")
    print("- Choose encode or decode from the menu.")
    print("- Paste any text directly; no shell quoting needed.")
    print("- End input with an empty line.")
    print("- For advanced settings, choose the prompt options when asked.")


def _select_encoder(encoders: Sequence[Encoder], name: Optional[str]) -> Encoder:
    by_name = {encoder.name: encoder for encoder in encoders}
    if name:
        encoder = by_name.get(name)
        if encoder is None:
            raise SystemExit(f"Unknown encoder: {name}")
        return encoder
    options = [encoder.name for encoder in encoders]
    print("Select encoder:")
    for idx, encoder in enumerate(encoders, start=1):
        print(f"{idx}. {encoder.name} - {encoder.description}")
    choice = _prompt_choice("Enter number or name: ", options, options[0])
    return by_name[choice]


def _encode_with_params(encoder: Encoder, text: str) -> str:
    name = encoder.name
    if name == "caesar":
        shift = _prompt_int("Shift (1-25): ", 1, 25)
        return encode_caesar(text, shift)
    if name == "fibonacci":
        seed = _prompt_choice(
            "Seed [0,1 or 1,1] (default 0,1): ", ["0,1", "1,1"], "0,1"
        )
        advance = _prompt_choice(
            "Advance on [alpha/all] (default alpha): ", ["alpha", "all"], "alpha"
        )
        seed_a, seed_b = (int(part) for part in seed.split(","))
        return encode_fibonacci(text, seed_a, seed_b, advance == "all")
    if name == "bacon":
        variant = _prompt_choice(
            "Bacon variant [classic/binary] (default classic): ",
            ["classic", "binary"],
            "classic",
        )
        return encode_bacon(text, variant)
    if name == "polybius":
        return encode_polybius(text)
    if name == "morse":
        return encode_morse(text)
    if name == "railfence":
        rails = _prompt_int("Rails (2-6): ", 2, 6)
        return encode_railfence(text, rails)
    if name == "scytale":
        cols = _prompt_int("Columns (2-6): ", 2, 6)
        return encode_scytale(text, cols)
    if encoder.func is None:
        raise SystemExit(f"Encoder requires parameters: {name}")
    return encoder.func(text)


def _format_output(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


def _print_results(
    items: Iterable[ScoredItem],
    show_hex: bool,
    max_chars: int,
) -> int:
    printed = 0
    for scored in items:
        chain = " -> ".join(scored.item.chain)
        print(
            f"[{chain}] abs={scored.abs_score:.2f} delta={scored.delta:+.2f} len={len(scored.item.data)}"
        )
        print(_format_output(scored.output_text, max_chars))
        if show_hex:
            print(scored.item.data.hex())
        print("")
        printed += 1
    return printed


def _select_decoders(all_decoders: Sequence[Decoder], names: Sequence[str]) -> List[Decoder]:
    if not names:
        return list(all_decoders)
    by_name = {decoder.name: decoder for decoder in all_decoders}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise SystemExit(f"Unknown decoder(s): {', '.join(missing)}")
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
) -> int:
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

    if show_all:
        filtered = scored_items
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
        filtered = filtered[:top]

    printed = _print_results(filtered, show_hex, max_chars)
    if printed == 0:
        raise SystemExit("No results matched the current filters.")
    return printed


def _interactive_loop(decoders: Sequence[Decoder], encoders: Sequence[Encoder]) -> None:
    menu = (
        "1) Decode\n"
        "2) Encode\n"
        "3) List decoders\n"
        "4) List encoders\n"
        "5) Help\n"
        "6) Quit\n"
    )
    while True:
        print(menu)
        choice = input("Select an option: ").strip().lower()
        if choice in {"6", "q", "quit", "exit"}:
            return
        if choice in {"5", "h", "help", "?"}:
            _print_interactive_help()
            continue
        if choice in {"3", "list", "decoders"}:
            for decoder in decoders:
                print(f"{decoder.name}: {decoder.description}")
            continue
        if choice in {"4", "encoders"}:
            for encoder in encoders:
                print(f"{encoder.name}: {encoder.description}")
            continue
        if choice in {"1", "d", "decode"}:
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            raw = input("Decoder(s) [all]: ").strip()
            if raw:
                decoder_names = [part for part in raw.replace(",", " ").split() if part]
            else:
                decoder_names = []
            advanced = _prompt_bool("Advanced settings", False)
            chain_depth = DEFAULT_CHAIN_DEPTH
            min_score = DEFAULT_MIN_SCORE
            min_delta = DEFAULT_MIN_DELTA
            show_all = False
            top = DEFAULT_TOP
            rank = DEFAULT_RANK
            max_per_decoder = DEFAULT_MAX_PER_DECODER
            max_results = DEFAULT_MAX_RESULTS
            show_hex = DEFAULT_SHOW_HEX
            max_chars = DEFAULT_MAX_CHARS
            if advanced:
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
                show_all = _prompt_bool("Show all results", False)
                top = _prompt_int(
                    f"Top results [{DEFAULT_TOP}]: ", 1, 50, DEFAULT_TOP
                )
                rank = _prompt_choice(
                    f"Rank mode [{DEFAULT_RANK}]: ",
                    ["absolute", "delta", "both"],
                    DEFAULT_RANK,
                )
                max_per_decoder = _prompt_int(
                    f"Max per decoder [{DEFAULT_MAX_PER_DECODER}]: ",
                    0,
                    10,
                    DEFAULT_MAX_PER_DECODER,
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
            try:
                _decode_text(
                    text,
                    decoders,
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
                )
            except SystemExit as exc:
                print(str(exc))
            continue
        if choice in {"2", "e", "encode"}:
            text = _prompt_text()
            if not text:
                print("No input provided.")
                continue
            encoder = _select_encoder(encoders, None)
            try:
                output = _encode_with_params(encoder, text)
            except ValueError as exc:
                print(str(exc))
                continue
            print(output)
            continue
        print("Unknown option. Enter 1-6 or 'q' to quit.")


def main() -> None:
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
    mode.add_argument("--decode", action="store_true", help="decode input (default)")
    mode.add_argument("--interactive", action="store_true", help="interactive menu")
    parser.add_argument("--list", action="store_true", help="list available decoders")
    parser.add_argument(
        "--list-encoders", action="store_true", help="list available encoders"
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

    args = parser.parse_args()
    decoders = get_decoders()
    encoders = get_encoders()

    if args.list:
        for decoder in decoders:
            print(f"{decoder.name}: {decoder.description}")
        return
    if args.list_encoders:
        for encoder in encoders:
            print(f"{encoder.name}: {encoder.description}")
        return

    if args.encode and args.decoder:
        raise SystemExit("Use --encoder with --encode (decoders are for decode mode).")

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
            raise SystemExit("Encode mode requires --encoder when input is piped.")
        encoder = _select_encoder(encoders, args.encoder)
        try:
            output = _encode_with_params(encoder, text)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(output)
        return

    _decode_text(
        text,
        decoders,
        args.decoder,
        args.chain_depth,
        args.min_score,
        args.min_delta,
        args.all,
        args.top,
        args.rank,
        args.max_per_decoder,
        args.max_results,
        args.show_hex,
        args.max_chars,
    )


if __name__ == "__main__":
    main()
