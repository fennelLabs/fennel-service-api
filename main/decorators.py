from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from main.models import APIGroup


def subject_to_api_limit(view_func):
    def wrap(request, *args, **kwargs):
        api_key = request.data.get("api_key", None)
        api_secret = request.data.get("api_secret", None)
        if api_key and api_secret:
            api_group = get_object_or_404(
                APIGroup, api_key=api_key, api_secret=api_secret
            )
            if not request.user in api_group.user_list.all():
                return Response(
                    {"error": "you don't have access to this api group"}, status=400
                )
            if not api_group.active:
                return Response(
                    {
                        "error": "API access restricted. Please contact info@fennellabs.com."
                    },
                    status=400,
                )
            api_group.request_counter += 1
            api_group.save()
            return view_func(request, *args, **kwargs)
        else:
            return Response({"error": "API key and secret required."}, status=400)

    return wrap
