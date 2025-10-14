"""
Debug test to see what's happening with admin permissions
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from main.models import UserKeys


class DebugAdminPermissions(TestCase):
    """Debug admin permission checks"""

    def setUp(self):
        """Set up test users"""
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            password='test123',
            email='regular@test.com'
        )
        UserKeys.objects.create(
            user=self.regular_user,
            mnemonic="bottom drive obey lake curtain smoke basket hold race lonely fit walk//Regular"
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            password='test123',
            email='staff@test.com',
            is_staff=True
        )
        UserKeys.objects.create(
            user=self.staff_user,
            mnemonic="bottom drive obey lake curtain smoke basket hold race lonely fit walk//Staff"
        )

    def test_regular_user_permissions(self):
        """Check regular user attributes"""
        print(f"\nRegular user: {self.regular_user.username}")
        print(f"  is_staff: {self.regular_user.is_staff}")
        print(f"  is_superuser: {self.regular_user.is_superuser}")
        print(f"  is_authenticated: {self.regular_user.is_authenticated}")
        
        assert self.regular_user.is_staff == False
        assert self.regular_user.is_superuser == False

    def test_staff_user_permissions(self):
        """Check staff user attributes"""
        print(f"\nStaff user: {self.staff_user.username}")
        print(f"  is_staff: {self.staff_user.is_staff}")
        print(f"  is_superuser: {self.staff_user.is_superuser}")
        print(f"  is_authenticated: {self.staff_user.is_authenticated}")
        
        assert self.staff_user.is_staff == True
        assert self.staff_user.is_superuser == False
