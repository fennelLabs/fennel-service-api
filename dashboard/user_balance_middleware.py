from dashboard.models import UserKeys


def user_balance_middleware(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            request.user.has_wallet = False
            request.user.balance = 0
            request.user.address = None
            request.user.api_group_name = None
            if request.user.api_group_users.exists():
                request.user.api_group_name = request.user.api_group_users.first().name
            if UserKeys.objects.filter(user=request.user.id).exists():
                request.user.has_wallet = (
                    UserKeys.objects.get(user=request.user.id).mnemonic is not None
                )
                if request.user.has_wallet:
                    request.user.balance = (
                        round(
                            int(UserKeys.objects.get(user=request.user.id).balance)
                            / 1000000000000,
                            4,
                        )
                        if UserKeys.objects.get(user=request.user.id).balance
                        else 0
                    )
                    request.user.address = UserKeys.objects.get(
                        user=request.user.id
                    ).address
        return get_response(request)

    return middleware
