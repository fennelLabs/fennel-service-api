from django import template

register = template.Library()

@register.filter
def pending_requests_count(group):
    """Return the count of pending join requests for a group."""
    return group.apigroupjoinrequest_set.filter(accepted=False, rejected=False).count()

@register.filter
def approved_requests_count(group):
    """Return the count of approved join requests for a group."""
    return group.apigroupjoinrequest_set.filter(accepted=True).count()

@register.filter
def rejected_requests_count(group):
    """Return the count of rejected join requests for a group."""
    return group.apigroupjoinrequest_set.filter(rejected=True).count()
