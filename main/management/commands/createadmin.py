"""
Defines a createadmin command extending manage.py.
"""
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Extends the BaseCommand class, providing tie-ins to Django.
    """

    def handle(self, *args, **options):
        """
        Carry out the command functionality.

        @param args:
        @param options:
        @return:
        """
        if not Group.objects.filter(name="FennelAdmin").exists():
            Group.objects.create(name="FennelAdmin")
        if not User.objects.filter(username="admin").exists():
            # CHANGE THE PASSWORD IN PRODUCTION!!!
            superuser = User.objects.create_superuser(
                "admin", "info@fennellabs.com", "Fennel-Admin"
            )
            superuser.first_name = "Admin"
            superuser.last_name = "User"
            superuser.save()
        else:
            superuser = User.objects.get(username="admin")
        if not superuser.groups.filter(name="FennelAdmin").exists():
            superuser.groups.add(Group.objects.get(name="FennelAdmin"))
