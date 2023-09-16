import os

from django.contrib import messages

from dashboard.models import Transaction, UserKeys

import requests


def create_wallet_with_userkeys(request, keys: UserKeys) -> None:
    if keys.mnemonic is not None and keys.mnemonic != "":
        messages.error(
            request,
            "Fennel wallet already exists.",
        )
        return
    response = requests.get(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account",
        timeout=5,
    )
    mnemonic = response.json()["mnemonic"]
    keys.mnemonic = mnemonic
    keys.save()
    if response.status_code != 200:
        messages.error(
            request,
            "Failed to create Fennel wallet.",
        )
    else:
        messages.success(
            request,
            "Fennel wallet created.",
        )


def check_balance(key: UserKeys) -> int:
    payload = {"mnemonic": key.mnemonic}
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
        data=payload,
        timeout=5,
    )
    if response.status_code != 200:
        return -1
    key.balance = response.json()["balance"]
    key.save()
    return int(response.json()["balance"])


def get_fee_for_transfer_token(recipient: str, amount: int, user_key: UserKeys) -> int:
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": recipient,
        "amount": amount,
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_transfer_token",
        data=payload,
        timeout=5,
    )
    if response.status_code != 200:
        return -1
    Transaction.objects.create(
        function="transfer_token",
        payload_size=0,
        fee=response.json()["fee"],
    )
    return int(response.json()["fee"])


def transfer_token(recipient: str, amount: int, user_key: UserKeys) -> None:
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": recipient,
        "amount": amount,
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token",
        data=payload,
        timeout=5,
    )
    if response.status_code != 200:
        return
    check_balance(user_key)
