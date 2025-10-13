"""
Test admin-only permissions for test message checkbox feature

Verifies that only administrators (staff or superuser) can use the
is_test_message parameter to convert messages to Test (T) type.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient, force_authenticate

from main.models import UserKeys


class TestAdminTestMessagePermissions(TestCase):
    """Test that only admins can create test messages"""

    def setUp(self):
        """Set up test users and API client"""
        self.client = APIClient()
        
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
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='test123',
            email='admin@test.com'
        )
        UserKeys.objects.create(
            user=self.superuser,
            mnemonic="bottom drive obey lake curtain smoke basket hold race lonely fit walk//Admin"
        )

    @patch('main.compound_views.signal_send_with_blockchain_data_helper')
    @patch('main.compound_views.whiteflag_encoder_helper')
    def test_regular_user_cannot_create_test_message(self, mock_encode, mock_send):
        """Regular users should get 403 when trying to create test messages"""
        mock_encode.return_value = ("encoded_message", True)
        mock_send.return_value = ({"success": True}, True)
        
        request_data = {
            "signal_body": {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "F",
                "text": "Test message",
                "referenceIndicator": "0",
                "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "is_test_message": True  # Regular user trying to create test message
        }
        
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/v1/whiteflag/encode_and_send_signal/', request_data, format='json')
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.content}"
        response_data = response.json()
        assert "error" in response_data
        assert "administrator" in response_data["error"].lower()
        
        # Encoder should not be called since we rejected early
        mock_encode.assert_not_called()

    @patch('main.compound_views.signal_send_with_blockchain_data_helper')
    @patch('main.compound_views.whiteflag_encoder_helper')
    def test_staff_user_can_create_test_message(self, mock_encode, mock_send):
        """Staff users should be able to create test messages"""
        mock_encode.return_value = ("encoded_message", True)
        mock_send.return_value = ({"success": True}, True)
        
        request_data = {
            "signal_body": {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "F",
                "text": "Test message",
                "referenceIndicator": "0",
                "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "is_test_message": True
        }
        
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post('/api/v1/whiteflag/encode_and_send_signal/', request_data, format='json')
        
        # Should succeed (status 200)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
        
        # Encoder should be called with Test message
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args[0]
        signal_body = call_args[0]
        assert signal_body["messageCode"] == "T"
        assert signal_body["pseudoMessageCode"] == "F"

    @patch('main.compound_views.signal_send_with_blockchain_data_helper')
    @patch('main.compound_views.whiteflag_encoder_helper')
    def test_superuser_can_create_test_message(self, mock_encode, mock_send):
        """Superusers should be able to create test messages"""
        mock_encode.return_value = ("encoded_message", True)
        mock_send.return_value = ({"success": True}, True)
        
        request_data = {
            "signal_body": {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "F",
                "text": "Test message",
                "referenceIndicator": "0",
                "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "is_test_message": True
        }
        
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post('/api/v1/whiteflag/encode_and_send_signal/', request_data, format='json')
        
        # Should succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
        
        # Encoder should be called with Test message
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args[0]
        signal_body = call_args[0]
        assert signal_body["messageCode"] == "T"
        assert signal_body["pseudoMessageCode"] == "F"

    @patch('main.compound_views.signal_send_with_blockchain_data_helper')
    @patch('main.compound_views.whiteflag_encoder_helper')
    def test_regular_user_can_send_regular_message(self, mock_encode, mock_send):
        """Regular users should still be able to send regular (non-test) messages"""
        mock_encode.return_value = ("encoded_message", True)
        mock_send.return_value = ({"success": True}, True)
        
        request_data = {
            "signal_body": {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "F",
                "text": "Regular message",
                "referenceIndicator": "0",
                "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "is_test_message": False  # Regular message
        }
        
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/v1/whiteflag/encode_and_send_signal/', request_data, format='json')
        
        # Should succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
        
        # Encoder should be called with original message (not converted to test)
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args[0]
        signal_body = call_args[0]
        assert signal_body["messageCode"] == "F"  # Still Free Text
        assert "pseudoMessageCode" not in signal_body

    @patch('main.compound_views.signal_send_with_blockchain_data_helper')
    @patch('main.compound_views.whiteflag_encoder_helper')
    def test_annotated_message_permissions(self, mock_encode, mock_send):
        """Test admin permissions for annotated messages endpoint"""
        mock_encode.return_value = ("encoded_message", True)
        mock_send.return_value = ({"success": True, "tx_hash": "0x123"}, True)
        
        request_data = {
            "signal_body": {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "F",
                "text": "Test message",
                "referenceIndicator": "0",
                "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "annotations": "This is a test annotation",
            "is_test_message": True
        }
        
        # Regular user should get 403
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/v1/whiteflag/send_signal_with_annotations/', request_data, format='json')
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.content}"
        
        # Staff user should succeed
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post('/api/v1/whiteflag/send_signal_with_annotations/', request_data, format='json')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"

    def test_omitting_is_test_message_defaults_to_false(self):
        """When is_test_message is omitted, it should default to False (backward compatible)"""
        # This is handled by serializer default value
        from main.serializers import EncodeAndSendSignalSerializer
        
        data = {
            "signal_body": {"messageCode": "F", "text": "Regular"}
            # is_test_message omitted
        }
        
        serializer = EncodeAndSendSignalSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data.get("is_test_message", False) == False
