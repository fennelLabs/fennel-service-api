from django.shortcuts import redirect, render
from django.contrib import messages

from silk.profiling.profiler import silk_profile

from dashboard.decorators import require_authentication
from dashboard.forms import CreateApiGroupForm
from dashboard.models import APIGroup


@silk_profile(name="index")
@require_authentication
def index(request):
    if request.user.api_group_admins.all().exists():
        return redirect(
            "dashboard:api_group_members",
            group_id=request.user.api_group_admins.first().id,
        )
    return render(request, "dashboard/index.html", {"form": CreateApiGroupForm()})


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
    return render(request, "dashboard/index.html", {"form": form})
