import os

from django.contrib import messages

from silk.profiling.profiler import silk_profile

from dashboard.models import Transaction, UserKeys

import requests


@silk_profile(name="create_wallet_with_userkeys")
def create_wallet_with_userkeys(request, keys: UserKeys) -> None:
    if keys.mnemonic is not None and keys.mnemonic != "":
        messages.error(
            request, "Fennel wallet already exists.",
        )
        return
    response = requests.get(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account", timeout=5,
    )
    mnemonic = response.json()["mnemonic"]
    keys.mnemonic = mnemonic
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address",
        data={"mnemonic": mnemonic},
        timeout=5,
    )
    keys.address = response.json()["address"]
    keys.save()
    if response.status_code != 200:
        messages.error(
            request, "Failed to create Fennel wallet.",
        )
    else:
        messages.success(
            request, "Fennel wallet created.",
        )


@silk_profile(name="import_account_with_mnemonic")
def import_account_with_mnemonic(request, mnemonic: str) -> None:
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address",
        data={"mnemonic": mnemonic},
        timeout=5,
    )
    if response.status_code != 200:
        messages.error(
            request, "Failed to import Fennel wallet.",
        )
        return
    if UserKeys.objects.filter(user=request.user).exists():
        keys = UserKeys.objects.filter(user=request.user)[0]
        keys.mnemonic = mnemonic
        keys.address = response.json()["address"]
        keys.save()
    else:
        UserKeys.objects.create(
            user=request.user, mnemonic=mnemonic, address=response.json()["address"],
        )
    messages.success(
        request, "Fennel wallet imported.",
    )


@silk_profile(name="check_balance")
def check_balance(key: UserKeys) -> int:
    payload = {"mnemonic": key.mnemonic}
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
            data=payload,
            timeout=5,
        )
    except requests.exceptions.ReadTimeout:
        return -1
    if response.status_code != 200:
        return -1
    key.balance = response.json()["balance"]
    key.save()
    return int(response.json()["balance"]) / 1000000000000


@silk_profile(name="get_fee_for_transfer_token")
def get_fee_for_transfer_token(recipient: str, amount: int, user_key: UserKeys) -> int:
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": recipient,
        "amount": amount,
    }
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_transfer_token",
            data=payload,
            timeout=5,
        )
    except requests.exceptions.ReadTimeout:
        return -1
    if response.status_code != 200:
        return -1
    Transaction.objects.create(
        function="transfer_token", payload_size=0, fee=response.json()["fee"],
    )
    return round(int(response.json()["fee"]) / 1000000000000, 4)


@silk_profile(name="transfer_token")
def transfer_token(recipient: str, amount: int, user_key: UserKeys) -> None:
    print("preparing request")
    math_response = requests.get(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/big_multiply",
        params={"a": amount, "b": 1000000000000},
        timeout=5,
    )
    if math_response.status_code != 200:
        return
    if not math_response.json()["success"]:
        return
    adjusted_value = math_response.json()["result"]
    print("sending adjusted value")
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": recipient,
        "amount": adjusted_value,
    }
    print("sending payload")
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token",
        data=payload,
        timeout=5,
    )
    print("response received")
    if response.status_code != 200:
        return
    check_balance(user_key)
