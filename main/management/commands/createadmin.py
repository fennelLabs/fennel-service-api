"""
Defines a createadmin command extending manage.py.
"""
from django.contrib.auth.models import User
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
        if not User.objects.filter(username="admin").exists():
            # CHANGE THE PASSWORD IN PRODUCTION!!!
            superuser = User.objects.create_superuser(
                "admin", "admin@admin.com", "Fennel-Admin"
            )
            superuser.first_name = "Admin"
            superuser.last_name = "User"
            superuser.save()
