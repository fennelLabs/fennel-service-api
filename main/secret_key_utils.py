"""
Thanks to https://www.geeksforgeeks.org/implementing-shamirs-secret-sharing-scheme-in-python/
for some of the functions in this module.
"""

import random
from decimal import Decimal

FIELD_SIZE = 10**5


def split_mnemonic(mnemonic):
    mnemonic_words = mnemonic.split(" ")
    mnemonic_integers = [convert_word_to_integer(word) for word in mnemonic_words]
    mnemonic_shares = [generate_shares(3, 2, integer) for integer in mnemonic_integers]
    share_group_one = [share[0] for share in mnemonic_shares]
    share_group_two = [share[1] for share in mnemonic_shares]
    share_group_three = [share[2] for share in mnemonic_shares]
    return [share_group_one, share_group_two, share_group_three]


def reconstruct_mnemonic(shares):
    mnemonic_integers = [
        reconstruct_secret([shares[0][i], shares[1][i]]) for i in range(len(shares[0]))
    ]
    mnemonic_words = [convert_integer_to_word(integer) for integer in mnemonic_integers]
    return " ".join(mnemonic_words)


def convert_word_to_integer(mnemonic: str) -> int:
    mnemonic_integers = [ord(word) for word in list(mnemonic)]
    mnemonic_strings = [str(integer) for integer in mnemonic_integers]
    padded_mnemonic_strings = [
        "0" * (3 - len(string)) + string for string in mnemonic_strings
    ]
    padded_mnemonic_strings.insert(0, "1")
    return int("".join(padded_mnemonic_strings))


def convert_integer_to_word(mnemonic: int) -> str:
    mnemonic_string = str(mnemonic)[1:]
    mnemonic_strings = [
        mnemonic_string[i : i + 3] for i in range(0, len(mnemonic_string), 3)
    ]
    mnemonic_integers = [int(word) for word in mnemonic_strings]
    mnemonic_characters = [chr(character) for character in mnemonic_integers]
    return "".join(mnemonic_characters)


def generate_shares(shares_count, threshold, secret):
    coefficients = coeff(threshold, secret)
    shares = []

    for _ in range(1, shares_count + 1):
        share_component = random.randrange(1, FIELD_SIZE)
        shares.append((share_component, polynom(share_component, coefficients)))

    return shares


def reconstruct_secret(shares):
    sums = 0

    for j, share_j in enumerate(shares):
        x_j_comp, y_j_comp = share_j
        prod = Decimal(1)

        for i, share_i in enumerate(shares):
            x_i_comp, _ = share_i
            if i != j:
                prod *= Decimal(Decimal(x_i_comp) / (x_i_comp - x_j_comp))

        prod *= y_j_comp
        sums += Decimal(prod)

    return int(round(Decimal(sums), 0))


def polynom(share_component, coefficients):
    point = 0
    for coefficient_index, coefficient_value in enumerate(coefficients[::-1]):
        point += share_component**coefficient_index * coefficient_value
    return point


def coeff(coeff_t, secret):
    coeff_value = [random.randrange(0, FIELD_SIZE) for _ in range(coeff_t - 1)]
    coeff_value.append(secret)
    return coeff_value
