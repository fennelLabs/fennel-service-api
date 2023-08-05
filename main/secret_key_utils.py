"""
Thanks to https://www.geeksforgeeks.org/implementing-shamirs-secret-sharing-scheme-in-python/
for some of the functions in this module.
"""

import random
from decimal import Decimal
from typing import List

FIELD_SIZE = 10**5


def split_mnemonic(mnemonic: str) -> List[int]:
    mnemonic_words = mnemonic.split(" ")
    mnemonic_integers = [__convert_word_to_integer(word) for word in mnemonic_words]
    mnemonic_shares = [
        __generate_shares(3, 2, integer) for integer in mnemonic_integers
    ]
    share_group_one = [share[0] for share in mnemonic_shares]
    share_group_two = [share[1] for share in mnemonic_shares]
    share_group_three = [share[2] for share in mnemonic_shares]
    return [share_group_one, share_group_two, share_group_three]


def reconstruct_mnemonic(shares: List[int]) -> str:
    mnemonic_integers = [
        __reconstruct_secret([shares[0][i], shares[1][i]])
        for i in range(len(shares[0]))
    ]
    mnemonic_words = [
        __convert_integer_to_word(integer) for integer in mnemonic_integers
    ]
    return " ".join(mnemonic_words)


def __convert_word_to_integer(mnemonic: str) -> int:
    mnemonic_integers = [ord(s) for s in list(mnemonic)]
    mnemonic_strings = [str(s) for s in mnemonic_integers]
    padded_mnemonic_strings = ["0" * (3 - len(s)) + s for s in mnemonic_strings]
    padded_mnemonic_strings.insert(0, "1")
    return int("".join(padded_mnemonic_strings))


def __convert_integer_to_word(mnemonic: int) -> str:
    mnemonic_string = str(mnemonic)[1:]
    mnemonic_strings = [
        mnemonic_string[i : i + 3] for i in range(0, len(mnemonic_string), 3)
    ]
    mnemonic_integers = [int(s) for s in mnemonic_strings]
    mnemonic_characters = [chr(s) for s in mnemonic_integers]
    return "".join(mnemonic_characters)


def __generate_shares(n, threshold, secret):
    coefficients = __coeff(threshold, secret)
    shares = []

    for _ in range(1, n + 1):
        x = random.randrange(1, FIELD_SIZE)
        shares.append((x, __polynom(x, coefficients)))

    return shares


def __reconstruct_secret(shares):
    sums = 0

    for j, share_j in enumerate(shares):
        xj, yj = share_j
        prod = Decimal(1)

        for i, share_i in enumerate(shares):
            xi, _ = share_i
            if i != j:
                prod *= Decimal(Decimal(xi) / (xi - xj))

        prod *= yj
        sums += Decimal(prod)

    return int(round(Decimal(sums), 0))


def __polynom(x, coefficients):
    point = 0
    for coefficient_index, coefficient_value in enumerate(coefficients[::-1]):
        point += x**coefficient_index * coefficient_value
    return point


def __coeff(t, secret):
    coeff = [random.randrange(0, FIELD_SIZE) for _ in range(t - 1)]
    coeff.append(secret)
    return coeff
