import os
from django.shortcuts import redirect, render
from django.contrib import messages

from silk.profiling.profiler import silk_profile

from dashboard.decorators import require_authentication
from dashboard.forms import CreateApiGroupForm, SendAPIGroupRequestForm
from dashboard.models import APIGroup, APIGroupJoinRequest, UserKeys

import requests


@silk_profile(name="index")
@require_authentication
def index(request):
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
