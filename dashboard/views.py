from django.shortcuts import redirect, render

from dashboard.decorators import require_authentication


@require_authentication
def index(request):
    if request.user.api_group_admins.all().exists():
        return redirect(
            "dashboard:api_group_members",
            group_id=request.user.api_group_admins.first().id,
        )
    return render(request, "dashboard/index.html")
