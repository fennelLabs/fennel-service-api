from django import template

from dashboard.models import UserKeys

register = template.Library()


@register.filter
def has_wallet(member):
    if not UserKeys.objects.filter(user=member.id).exists():
        return False
    return UserKeys.objects.get(user=member.id).mnemonic is not None


@register.filter
def get_balance(member):
    if not UserKeys.objects.filter(user=member.id).exists():
        return 0
    if not UserKeys.objects.get(user=member.id).balance:
        return 0
    return round(int(UserKeys.objects.get(user=member.id).balance) / 1000000000000, 4)


@register.filter
def get_address(member):
    if not UserKeys.objects.filter(user=member.id).exists():
        return None
    return UserKeys.objects.get(user=member.id).address
