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


def test_cli_info_caesar(capsys):
    _run_cli(["--info", "caesar"])
    captured = capsys.readouterr()
    assert "Caesar Cipher" in captured.out
    assert "Julius Caesar" in captured.out
    assert "Historical context" in captured.out


def test_cli_info_vigenere(capsys):
    _run_cli(["--info", "vigenere"])
    captured = capsys.readouterr()
    assert "Vigenère Cipher" in captured.out
    assert "polyalphabetic" in captured.out.lower()


def test_cli_info_unknown(capsys):
    _run_cli(["--info", "nonexistent"])
    captured = capsys.readouterr()
    assert "No glossary entry found" in captured.out


def test_cli_ctf_flag_not_filtered(capsys):
    # Test that CTF flags are not filtered out even with low English scores
    # Base64 encoded: picoCTF{example_fl4g_w1th_numb3rs!}
    _run_cli(["cGljb0NURntleGFtcGxlX2ZsNGdfdzF0aF9udW1iM3JzIX0="])
    captured = capsys.readouterr()
    # The decoded flag should appear in the output
    assert "picoCTF{example_fl4g_w1th_numb3rs!}" in captured.out


def test_cli_ctf_flag_various_formats(capsys):
    # Test different CTF flag formats are all detected and not filtered
    test_cases = [
        ("ZmxhZ3tzaW1wbGVfdGVzdH0=", "flag{simple_test}"),  # flag{...}
        ("SFRCe2hhY2tfdGhlX2JveH0=", "HTB{hack_the_box}"),  # HTB{...}
        ("RFVDVEZ7ZG93bl91bmRlcn0=", "DUCTF{down_under}"),  # DUCTF{...}
        ("Q1RGe2dlbmVyaWNfZmxhZ30=", "CTF{generic_flag}"),  # CTF{...}
    ]

    for encoded, expected_flag in test_cases:
        _run_cli([encoded])
        captured = capsys.readouterr()
        assert expected_flag in captured.out, f"Flag {expected_flag} not found in output"


def test_cli_ctf_flag_with_different_ciphers(capsys):
    # Test CTF flags encoded with different ciphers
    # ROT13: picoCTF{test_flag_123} -> cvpbPGS{grfg_synt_123}
    _run_cli(["cvpbPGS{grfg_synt_123}"])
    captured = capsys.readouterr()
    assert "picoCTF{test_flag_123}" in captured.out

    # Hex: picoCTF{test_flag_123}
    _run_cli(["7069636f4354467b746573745f666c61675f3132337d"])
    captured = capsys.readouterr()
    assert "picoCTF{test_flag_123}" in captured.out

    # URL encoded: picoCTF{test_flag_123}
    _run_cli(["picoCTF%7Btest_flag_123%7D"])
    captured = capsys.readouterr()
    assert "picoCTF{test_flag_123}" in captured.out


def test_cli_regular_text_still_filtered(capsys):
    # Verify that regular text without CTF patterns is still filtered normally
    # Base64 encoded: "This is just regular text without any special patterns"
    _run_cli(["VGhpcyBpcyBqdXN0IHJlZ3VsYXIgdGV4dCB3aXRob3V0IGFueSBzcGVjaWFsIHBhdHRlcm5z"])
    captured = capsys.readouterr()
    # Should show the decoded text (high English score)
    assert "This is just regular text without any special patterns" in captured.out
    # The base64 result should appear near the top (high score)
    lines = captured.out.split('\n')
    base64_line_idx = None
    for idx, line in enumerate(lines):
        if "This is just regular text" in line:
            base64_line_idx = idx
            break
    # The high-scoring result should appear in the first 10 lines
    assert base64_line_idx is not None and base64_line_idx < 10, \
        "High-scoring regular text should appear near the top"
