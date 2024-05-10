import os
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.messages.storage import default_storage

from silk.profiling.profiler import silk_profile

from dashboard.decorators import require_admin, require_authentication
from dashboard.forms import (
    CreateApiGroupForm,
    ImportWalletForm,
    SendAPIGroupRequestForm,
    TransferTokenToAddressForm,
)
from dashboard.models import APIGroup, APIGroupJoinRequest, UserKeys
from dashboard.blockchain_helpers import (
    check_balance,
    get_fee_for_transfer_token,
    import_account_with_mnemonic,
    transfer_token,
)

import requests


@silk_profile(name="index")
@require_authentication
def index(request):
    request._messages = default_storage(request)
    if request.user.api_group_admins.all().exists():
        return redirect(
            "dashboard:api_group_members",
            group_id=request.user.api_group_admins.first().id,
        )
    return render(
        request,
        "dashboard/index.html",
        {"form": CreateApiGroupForm(), "join_request_form": SendAPIGroupRequestForm()},
    )


@silk_profile(name="send_group_join_request")
@require_authentication
def send_group_join_request(request):
    if request.method == "POST":
        join_form = SendAPIGroupRequestForm(request.POST)
        if not join_form.is_valid():
            return render(
                request,
                "dashboard/index.html",
                {"form": CreateApiGroupForm(), "join_request_form": join_form},
            )
        group_name = join_form.cleaned_data.get("group_name")
        if group_name:
            group = APIGroup.objects.filter(name=group_name).first()
            if group:
                APIGroupJoinRequest.objects.create(api_group=group, user=request.user)
                group.save()
                messages.success(request, f"Sent join request to {group.name}.")
                return redirect("dashboard:index")
    else:
        join_form = SendAPIGroupRequestForm()
    return render(
        request,
        "dashboard/index.html",
        {"form": CreateApiGroupForm(), "join_request_form": join_form},
    )


@silk_profile(name="create_api_group")
@require_authentication
def create_api_group(request):
    if request.method == "POST":
        form = CreateApiGroupForm(request.POST)
        if not form.is_valid():
            return render(request, "dashboard/index.html", {"form": form})
        group_name = form.cleaned_data.get("group_name")
        if group_name:
            group = APIGroup.objects.create(name=group_name)
            group.admin_list.add(request.user)
            group.user_list.add(request.user)
            group.save()
            messages.success(request, f"Created API group {group.name}.")
            return redirect("dashboard:api_group_members", group_id=group.id)
    else:
        form = CreateApiGroupForm()
    return render(
        request,
        "dashboard/index.html",
        {"form": form, "join_request_form": SendAPIGroupRequestForm()},
    )


@silk_profile(name="import_wallet")
@require_authentication
def import_wallet(request, group_id=None):
    if request.method == "POST":
        form = ImportWalletForm(request.POST)
        if not form.is_valid():
            print("form is not valid")
            return render(
                request,
                "dashboard/import_wallet.html",
                {"form": form, "group_id": group_id},
            )
        import_account_with_mnemonic(request, form.cleaned_data.get("mnemonic"))
        return redirect("dashboard:api_group_members", group_id=group_id)
    form = ImportWalletForm()
    return render(
        request, "dashboard/import_wallet.html", {"form": form, "group_id": group_id}
    )


@silk_profile(name="transfer_tokens_to_address_post")
def __tranfer_tokens_to_address_post(request, form, user_key, group_id):
    amount = form.cleaned_data.get("amount")
    address = form.cleaned_data.get("address")
    balance = check_balance(user_key)
    fee = get_fee_for_transfer_token(address, amount, user_key)
    if balance == -1:
        messages.error(
            request,
            "There was an error checking your balance. Please try again later.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if fee == -1:
        messages.error(
            request,
            "There was an error checking the fee for this transaction. Please try again later.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if balance < amount + fee:
        messages.error(
            request,
            "You do not have enough tokens to complete this transaction.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    return render(
        request,
        "dashboard/confirm_transfer_tokens_address.html",
        {
            "group_id": group_id,
            "address": address,
            "fee": round(fee / 1000000000000, 4),
            "amount": amount,
        },
    )


@silk_profile(name="transfer_tokens_to_address")
@require_authentication
@require_admin
def transfer_tokens_to_address(request, group_id=None):
    messages.get_messages(request).used = True
    user_key = get_object_or_404(UserKeys, user=request.user)
    if not user_key.mnemonic:
        messages.error(
            request,
            "You have not created a Fennel wallet yet.",
        )
        return redirect("dashboard:index", group_id=group_id)
    if request.method == "GET":
        form = TransferTokenToAddressForm()
    if request.method == "POST":
        form = TransferTokenToAddressForm(request.POST)
        if form.is_valid():
            return __tranfer_tokens_to_address_post(request, form, user_key, group_id)
    return render(
        request,
        "dashboard/transfer_tokens_address.html",
        {"group_id": group_id, "form": form},
    )


@silk_profile(name="confirm_transfer_tokens_to_address")
@require_authentication
@require_admin
def confirm_transfer_tokens_to_address(request, group_id=None):
    user_key = get_object_or_404(UserKeys, user=request.user)
    amount = request.POST.get("amount")
    address = request.POST.get("address")
    transfer_token(address, amount, user_key)
    return redirect("dashboard:index", group_id=group_id)


@silk_profile(name="get_balance")
@require_authentication
def get_balance(request):
    if not UserKeys.objects.filter(user=request.user).exists():
        messages.error(request, "You do not have a wallet.")
        return redirect("dashboard:index")
    keys = UserKeys.objects.get(user=request.user)
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
        data={"mnemonic": keys.mnemonic},
        timeout=5,
    )
    if response.status_code != 200:
        messages.error(
            request,
            "Subservice is not available. Try again later, or contact us at info@fennellabs.com.",
        )
        return redirect("dashboard:index")
    keys.balance = response.json()["balance"]
    keys.save()
    return redirect("dashboard:index")


@silk_profile(name="get_balance_for_member")
@require_authentication
def get_balance_for_member(request, group_id, member_id):
    if not UserKeys.objects.filter(user__pk=member_id).exists():
        messages.error(request, "That user does not have a wallet.")
        return redirect("dashboard:api_group_members", group_id=group_id)
    keys = UserKeys.objects.get(user=request.user)
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
            data={"mnemonic": keys.mnemonic},
            timeout=5,
        )
    except requests.exceptions.ReadTimeout:
        messages.error(
            request,
            "Subservice is not available. Try again later, or contact us at info@fennellabs.com.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if response.status_code != 200:
        messages.error(
            request,
            "Subservice is not available. Try again later, or contact us at info@fennellabs.com.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    keys.balance = response.json()["balance"]
    keys.save()
    return redirect("dashboard:api_group_members", group_id=group_id)
