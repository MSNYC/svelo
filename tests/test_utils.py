from svelo.utils import english_score, hexlike_ratio, is_ctf_flag, similarity_ratio


def test_english_score_prefers_plaintext():
    plaintext = "The cock crows at dawn."
    hexlike = "54686520636f636b2063726f7773206174206461776e2e"
    assert english_score(plaintext) > english_score(hexlike)


def test_hexlike_ratio():
    hexlike = "54686520636f636b2063726f7773206174206461776e2e"
    plaintext = "The cock crows at dawn."
    assert hexlike_ratio(hexlike) > 0.9
    assert hexlike_ratio(plaintext) < 0.8


def test_similarity_ratio():
    assert similarity_ratio("abcdef", "abcdef") > 0.9
    assert similarity_ratio("abcdef", "123456") < 0.2
    assert similarity_ratio("short", "a much longer string") < 0.5


def test_is_ctf_flag_detects_common_patterns():
    # Test common CTF flag formats
    assert is_ctf_flag("picoCTF{example_fl4g_w1th_numb3rs!}")
    assert is_ctf_flag("flag{test_flag}")
    assert is_ctf_flag("CTF{example}")
    assert is_ctf_flag("HTB{hack_the_box}")
    assert is_ctf_flag("DUCTF{down_under}")

    # Test with whitespace
    assert is_ctf_flag("  picoCTF{test}  ")

    # Test non-flag patterns
    assert not is_ctf_flag("This is just regular text")
    assert not is_ctf_flag("No braces here")
    assert not is_ctf_flag("")
    assert not is_ctf_flag("   ")

    # Test edge cases
    assert not is_ctf_flag("{missing_prefix}")
    assert is_ctf_flag("a{valid}")  # Single char prefix is valid
