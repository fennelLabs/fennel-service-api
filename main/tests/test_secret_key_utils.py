from main.secret_key_utils import (
    __generate_shares,
    __reconstruct_secret,
    __convert_word_to_integer,
    __convert_integer_to_word,
    reconstruct_mnemonic,
    split_mnemonic,
)


def test_secret_shares():
    shares = __generate_shares(5, 3, 123456789)
    assert __reconstruct_secret(shares[:3]) == 123456789


def test_secret_shares_2():
    shares = __generate_shares(5, 3, 123456789)
    assert __reconstruct_secret(shares[1:4]) == 123456789


def test_secret_shares_3():
    shares = __generate_shares(5, 3, 123456789)
    assert __reconstruct_secret(shares[2:5]) == 123456789


def test_secret_shares_4():
    shares = __generate_shares(5, 3, 123456789)
    assert __reconstruct_secret([shares[0], shares[2], shares[4]]) == 123456789


def test_secret_shares_5():
    shares = __generate_shares(3, 2, 123456789)
    assert __reconstruct_secret([shares[0], shares[1]]) == 123456789


def test_mnemonic_encoding():
    test_value = "captain calm afraid vehicle fetch stage custom federal assist arrange pumpkin cheese grocery square discover firm kind endorse door tonight name lonely alter wrestle"
    encoded_value = __convert_word_to_integer(test_value)
    assert encoded_value is not None
    assert encoded_value > 0
    decoded_value = __convert_integer_to_word(encoded_value)
    assert decoded_value is not None
    assert decoded_value == test_value


def test_split_mnemonic():
    test_value = "captain calm afraid vehicle fetch stage custom federal assist arrange pumpkin cheese grocery square discover firm kind endorse door tonight name lonely alter wrestle"
    shares = split_mnemonic(test_value)
    assert shares is not None
    assert len(shares) == 3
    assert shares[0] is not None
    assert shares[1] is not None
    assert shares[2] is not None
    assert len(shares[0]) == 24
    assert len(shares[1]) == 24
    assert len(shares[2]) == 24


def test_reconstruct_mnemonic():
    test_value = "captain calm afraid vehicle fetch stage custom federal assist arrange pumpkin cheese grocery square discover firm kind endorse door tonight name lonely alter wrestle"
    shares = split_mnemonic(test_value)
    assert shares is not None
    assert len(shares) == 3
    assert shares[0] is not None
    assert shares[1] is not None
    assert shares[2] is not None
    assert len(shares[0]) == 24
    assert len(shares[1]) == 24
    assert len(shares[2]) == 24
    reconstructed_value = reconstruct_mnemonic([shares[0], shares[1]])
    assert reconstructed_value is not None
    assert reconstructed_value == test_value


def test_check_split_string():
    integer = __convert_word_to_integer("captain")
    print(integer)
    word = __convert_integer_to_word(integer)
    assert word == "captain"
    shares = __generate_shares(3, 2, integer)
    reconstructed_integer = __reconstruct_secret([shares[0], shares[1]])
    assert integer == reconstructed_integer
    reconstructed_word = __convert_integer_to_word(reconstructed_integer)
    assert reconstructed_word == "captain"


def test_check_reconstruct_one_integer():
    test_value = "captain calm afraid vehicle fetch stage custom federal assist arrange pumpkin cheese grocery square discover firm kind endorse door tonight name lonely alter wrestle"
    words = test_value.split(" ")
    integer = __convert_word_to_integer(words[0])
    shares = __generate_shares(3, 2, integer)
    reconstructed_integer = __reconstruct_secret([shares[0], shares[1]])
    assert integer == reconstructed_integer
