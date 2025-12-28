from svelo.utils import english_score, hexlike_ratio, similarity_ratio


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
