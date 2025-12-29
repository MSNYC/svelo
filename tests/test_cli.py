import io
import sys

import pytest

from svelo.cli import main


class _Stdin(io.StringIO):
    def isatty(self) -> bool:
        return False


def _run_cli(args, stdin_text=None):
    argv = ["svelo"] + args
    stdin = sys.stdin
    stdout = sys.stdout
    try:
        sys.argv = argv
        if stdin_text is not None:
            sys.stdin = _Stdin(stdin_text)
        main()
    finally:
        sys.argv = ["svelo"]
        sys.stdin = stdin
        sys.stdout = stdout


def test_list_decoders(capsys):
    _run_cli(["--list"])
    captured = capsys.readouterr()
    assert "base64" in captured.out


def test_list_encoders(capsys):
    _run_cli(["--list-encoders"])
    captured = capsys.readouterr()
    assert "base64" in captured.out


def test_cli_encode_hex(capsys):
    _run_cli(["--encode", "--encoder", "hex", "Hello"])
    captured = capsys.readouterr()
    assert "48656c6c6f" in captured.out


def test_cli_base64_decode(capsys):
    _run_cli(["SGVsbG8=", "--decoder", "base64"])  # prints decoded output
    captured = capsys.readouterr()
    assert "Hello" in captured.out


def test_cli_fibonacci_decode_roundtrip(capsys):
    _run_cli(["Mbsm Vhphgh", "--decoder", "fibonacci"])
    captured = capsys.readouterr()
    assert "Mark Schulz" in captured.out


def test_cli_stdin_decode(capsys):
    _run_cli(["--decoder", "hex"], stdin_text="48656c6c6f")
    captured = capsys.readouterr()
    assert "Hello" in captured.out


def test_cli_no_results():
    with pytest.raises(SystemExit):
        _run_cli(["!!!"])
