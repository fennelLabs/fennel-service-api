from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from silk.profiling.profiler import silk_profile

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
    return render(request, "admin/request_list.html", {"requests": join_requests})


@silk_profile(name="accept_join_request")
@require_admin
@require_authentication
def accept_join_request(request, group_id=None, request_id=None):
    request_obj = APIGroupJoinRequest.objects.get(id=request_id)
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
    group = APIGroup.objects.get(id=group_id)
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
        "admin/member_list.html",
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
        "admin/confirm_transfer_tokens.html",
        {
            "group_id": group_id,
            "member_id": member.id,
            "fee": fee,
            "amount": amount,
        },
    )


@silk_profile(name="transfer_tokens_to_member")
@require_admin
@require_authentication
def transfer_tokens_to_member(request, group_id=None, member_id=None):
    member = get_object_or_404(UserKeys, user__pk=member_id)
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
        "admin/transfer_tokens.html",
        {"group_id": group_id, "member_id": member.id, form: form},
    )


@silk_profile(name="confirm_transfer_tokens_to_member")
@require_admin
@require_authentication
def confirm_transfer_tokens_to_member(request, group_id=None, member_id=None):
    member = get_object_or_404(UserKeys, user__pk=member_id)
    user_key = get_object_or_404(UserKeys, user=request.user)
    amount = request.POST.get("amount")
    transfer_token(member.address, amount, user_key)
    return redirect("dashboard:api_group_members", group_id=group_id)


@silk_profile(name="remove_group_member")
@require_admin
@require_authentication
def remove_group_member(request, group_id=None, member_id=None):
    group = APIGroup.objects.get(id=group_id)
    member = get_object_or_404(User, id=member_id)
    group.user_list.remove(member)
    return redirect("dashboard:api_group_members", group_id=group_id)
