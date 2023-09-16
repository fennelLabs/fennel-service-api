from django.shortcuts import redirect, render
from dashboard.blockchain_helpers import (
    check_balance,
    get_fee_for_transfer_token,
    transfer_token,
)

from dashboard.decorators import (
    require_admin,
    require_authentication,
    require_mnemonic_created,
)
from dashboard.forms import TransferTokenForm
from dashboard.models import APIGroup, APIGroupJoinRequest, User, UserKeys


@require_admin
@require_authentication
def api_group_join_requests(request, group_id=None):
    group = APIGroup.objects.get(id=group_id)
    requests = APIGroupJoinRequest.objects.filter(
        rejected=False, accepted=False, api_group=group
    )
    return render(request, "admin/request_list.html", {"requests": requests})


@require_admin
@require_authentication
def accept_join_request(request, group_id=None, request_id=None):
    request_obj = APIGroupJoinRequest.objects.get(id=request_id)
    request_obj.accepted = True
    request_obj.save()
    return redirect("dashboard:api_group_join_requests", group_id=group_id)


@require_admin
@require_authentication
def reject_join_request(request, group_id=None, request_id=None):
    request_obj = APIGroupJoinRequest.objects.get(id=request_id)
    request_obj.rejected = True
    request_obj.save()
    return redirect("dashboard:api_group_join_requests", group_id=group_id)


@require_admin
@require_authentication
def api_group_members(request, group_id=None):
    group = APIGroup.objects.get(id=group_id)
    members = group.user_list.all()
    return render(
        request, "admin/member_list.html", {"members": members, "group_id": group.id}
    )


@require_mnemonic_created
@require_admin
@require_authentication
def transfer_tokens_to_member(request, group_id=None, member_id=None):
    group = APIGroup.objects.get(id=group_id)
    member = UserKeys.objects.get(id=member_id)
    user_key = UserKeys.objects.get(user=request.user)
    if request.method == "GET":
        form = TransferTokenForm()
    if request.method == "POST":
        form = TransferTokenForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data.get("amount")
            balance = check_balance(user_key)
            fee = get_fee_for_transfer_token(member.address, amount, user_key)
            if balance == -1 or fee == -1:
                return render(
                    request,
                    "admin/failed_to_access_blockchain.html",
                    {"group_id": group.id, "member_id": member.id},
                )
            if balance < amount + fee:
                return render(
                    request,
                    "admin/insufficient_balance.html",
                    {"group_id": group.id, "member_id": member.id},
                )
            return render(
                request,
                "admin/confirm_transfer_tokens.html",
                {
                    "group_id": group.id,
                    "member_id": member.id,
                    "fee": fee,
                    "amount": amount,
                },
            )
    return render(
        request,
        "admin/transfer_tokens.html",
        {"group_id": group.id, "member_id": member.id, form: form},
    )


@require_mnemonic_created
@require_admin
@require_authentication
def confirm_transfer_tokens_to_member(request, group_id=None, member_id=None):
    member = UserKeys.objects.get(id=member_id)
    user_key = UserKeys.objects.get(user=request.user)
    amount = request.POST.get("amount")
    transfer_token(member.address, amount, user_key)
    return redirect("dashboard:api_group_members", group_id=group_id)


@require_admin
@require_authentication
def remove_group_member(request, group_id=None, member_id=None):
    group = APIGroup.objects.get(id=group_id)
    member = User.objects.get(id=member_id)
    group.user_list.remove(member)
    return redirect("dashboard:api_group_members", group_id=group_id)
