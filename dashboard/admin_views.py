import os
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from silk.profiling.profiler import silk_profile

import requests

from dashboard.blockchain_helpers import (
    check_balance,
    create_wallet_with_userkeys,
    get_fee_for_transfer_token,
    transfer_token,
)
from dashboard.decorators import (
    require_admin,
    require_authentication,
)
from dashboard.forms import TransferTokenForm
from dashboard.models import APIGroup, APIGroupJoinRequest, User, UserKeys


@silk_profile(name="api_group_join_requests")
@require_admin
@require_authentication
def api_group_join_requests(request, group_id=None):
    group = APIGroup.objects.get(id=group_id)
    join_requests = APIGroupJoinRequest.objects.filter(
        rejected=False, accepted=False, api_group=group
    )
    return render(
        request,
        "dashboard/request_list.html",
        {"requests": join_requests, "group_id": group_id},
    )


@silk_profile(name="accept_join_request")
@require_admin
@require_authentication
def accept_join_request(request, group_id=None, request_id=None):
    request_obj = APIGroupJoinRequest.objects.get(id=request_id)
    request_obj.api_group.user_list.add(request_obj.user)
    request_obj.accepted = True
    request_obj.save()
    return redirect("dashboard:api_group_join_requests", group_id=group_id)


@silk_profile(name="reject_join_request")
@require_admin
@require_authentication
def reject_join_request(request, group_id=None, request_id=None):
    request_obj = APIGroupJoinRequest.objects.get(id=request_id)
    request_obj.rejected = True
    request_obj.save()
    return redirect("dashboard:api_group_join_requests", group_id=group_id)


@silk_profile(name="api_group_members")
@require_admin
@require_authentication
def api_group_members(request, group_id=None):
    messages.get_messages(request).used = True
    group = get_object_or_404(APIGroup, id=group_id)
    members = group.user_list.all()

    if (
        UserKeys.objects.filter(user=request.user).exists()
        and UserKeys.objects.get(user=request.user).mnemonic is not None
    ):
        account_created = True
    else:
        messages.error(
            request,
            "You must create a Fennel wallet to send tokens to your API Group members.",
        )
        account_created = False

    return render(
        request,
        "dashboard/member_list.html",
        {
            "members": members,
            "group_id": group.id,
            "account_created": account_created,
        },
    )


@silk_profile(name="create_wallet")
@require_admin
@require_authentication
def create_wallet(request, group_id=None):
    if not UserKeys.objects.filter(user=request.user).exists():
        keys = UserKeys.objects.create(user=request.user)
    else:
        keys = UserKeys.objects.get(user=request.user)
    create_wallet_with_userkeys(request, keys)
    return redirect("dashboard:api_group_members", group_id=group_id)


@silk_profile(name="create_wallet_for_member")
@require_admin
@require_authentication
def create_wallet_for_member(request, group_id=None, member_id=None):
    member = User.objects.get(id=member_id)
    if not UserKeys.objects.filter(user=member).exists():
        keys = UserKeys.objects.create(user=member)
    else:
        keys = UserKeys.objects.get(user=member)
    create_wallet_with_userkeys(request, keys)
    return redirect("dashboard:api_group_members", group_id=group_id)


@silk_profile(name="transfer_tokens_to_member_post")
def __tranfer_tokens_to_member_post(request, form, user_key, member, group_id):
    amount = form.cleaned_data.get("amount")
    username = member.user.username
    balance = check_balance(user_key)
    fee = get_fee_for_transfer_token(member.address, amount, user_key)
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
        "dashboard/confirm_transfer_tokens_to_member.html",
        {
            "group_id": group_id,
            "member_id": member.id,
            "fee": round(fee / 1000000000000, 4),
            "amount": amount,
            "username": username,
        },
    )


@silk_profile(name="transfer_tokens_to_member")
@require_admin
@require_authentication
def transfer_tokens_to_member(request, group_id=None, member_id=None):
    messages.get_messages(request).used = True
    member = get_object_or_404(UserKeys, user__pk=member_id)
    recipient = member.user
    if not member.mnemonic:
        messages.error(
            request,
            "This member has not created a Fennel wallet yet.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    user_key = get_object_or_404(UserKeys, user=request.user)
    if not user_key.mnemonic:
        messages.error(
            request,
            "You have not created a Fennel wallet yet.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if request.method == "GET":
        form = TransferTokenForm()
    if request.method == "POST":
        form = TransferTokenForm(request.POST)
        if form.is_valid():
            return __tranfer_tokens_to_member_post(
                request, form, user_key, member, group_id
            )
    return render(
        request,
        "dashboard/transfer_tokens.html",
        {
            "group_id": group_id,
            "member_id": member.id,
            "form": form,
            "username": recipient.username,
        },
    )


@silk_profile(name="confirm_transfer_tokens_to_member")
@require_admin
@require_authentication
def confirm_transfer_tokens_to_member(request, group_id=None, member_id=None):
    member = get_object_or_404(UserKeys, user__pk=member_id)
    user_key = get_object_or_404(UserKeys, user=request.user)
    amount = request.POST.get("amount")
    print("confirming transfer of tokens")
    result = transfer_token(member.address, amount, user_key)
    if result["status"] == -1:
        messages.error(
            request,
            result["message"],
        )
    else:
        messages.success(
            request,
            f"Successfully transferred {amount} tokens to {member.user.username}.",
        )
    return redirect("dashboard:api_group_members", group_id=group_id)


@silk_profile(name="remove_group_member")
@require_admin
@require_authentication
def remove_group_member(request, group_id=None, member_id=None):
    messages.get_messages(request).used = True
    group = APIGroup.objects.get(id=group_id)
    member = get_object_or_404(User, id=member_id)
    if not group.user_list.filter(id=member_id).exists():
        messages.error(
            request,
            "This user is not a member of this API Group.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if group.admin_list.filter(id=member_id).exists():
        messages.error(
            request,
            "You cannot remove an admin from an API Group.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    if member == request.user:
        messages.error(
            request,
            "You cannot remove yourself from an API Group.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    group.user_list.remove(member)
    return redirect("dashboard:api_group_members", group_id=group_id)


@silk_profile(name="generate_group_encryption_keys")
@require_admin
@require_authentication
def generate_group_encryption_keys(request, group_id=None):
    messages.get_messages(request).used = True
    group = get_object_or_404(APIGroup, id=group_id)
    if group.public_diffie_hellman_key:
        messages.error(
            request,
            "This API Group already has encryption keys.",
        )
        return redirect("dashboard:api_group_members", group_id=group_id)
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/generate_encryption_channel",
        timeout=5,
    )
    group.public_diffie_hellman_key = response.json()["secret"]
    group.private_diffie_hellman_key = response.json()["public"]
    group.save()
    return redirect("dashboard:api_group_members", group_id=group_id)
