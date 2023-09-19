from dashboard.models import UserKeys


def user_balance_middleware(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            request.user.has_wallet = False
            request.user.balance = 0
            request.user.address = None
            if UserKeys.objects.filter(user=request.user.id).exists():
                request.user.has_wallet = (
                    UserKeys.objects.get(user=request.user.id).mnemonic is not None
                )
                if request.user.has_wallet:
                    request.user.balance = (
                        int(UserKeys.objects.get(user=request.user.id).balance)
                        if UserKeys.objects.get(user=request.user.id).balance
                        else 0
                    )
                    request.user.address = UserKeys.objects.get(
                        user=request.user.id
                    ).address
        return get_response(request)

    return middleware
