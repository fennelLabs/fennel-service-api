def get_api_group_public_key(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            request.user.api_group_public_key = None
            if request.user.api_group_admins.all().exists():
                request.user.api_group_public_key = (
                    request.user.api_group_admins.all()
                    .first()
                    .public_diffie_hellman_key
                )
        return get_response(request)

    return middleware
