"""
Test the convert_to_test_message helper function
"""

from django.test import TestCase
from main.whiteflag_helpers import convert_to_test_message


class TestConvertToTestMessage(TestCase):
    """Test converting regular messages to Test (T) messages"""

    def test_convert_free_text_to_test_message(self):
        """Free Text message should convert to Test message with pseudoMessageCode F"""
        free_text_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": "Hello World",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        test_message = convert_to_test_message(free_text_message)

        # Should be converted to Test message
        assert test_message["messageCode"] == "T"
        assert test_message["pseudoMessageCode"] == "F"
        
        # All other fields should be preserved
        assert test_message["text"] == "Hello World"
        assert test_message["prefix"] == "WF"
        assert test_message["version"] == "1"

    def test_convert_authentication_to_test_message(self):
        """Authentication message should convert to Test message with pseudoMessageCode A"""
        auth_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "verificationMethod": "1",
            "verificationData": "https://example.com",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        test_message = convert_to_test_message(auth_message)

        assert test_message["messageCode"] == "T"
        assert test_message["pseudoMessageCode"] == "A"
        assert test_message["verificationData"] == "https://example.com"

    def test_convert_resource_to_test_message(self):
        """Resource message should convert to Test message with pseudoMessageCode R"""
        resource_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "R",
            "resourceMethod": "1",
            "resourceData": "https://example.com/resource",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        test_message = convert_to_test_message(resource_message)

        assert test_message["messageCode"] == "T"
        assert test_message["pseudoMessageCode"] == "R"
        assert test_message["resourceData"] == "https://example.com/resource"

    def test_already_test_message_unchanged(self):
        """If message is already a Test message, it should remain unchanged"""
        test_message_input = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",
            "pseudoMessageCode": "F",
            "text": "Already a test",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        test_message_output = convert_to_test_message(test_message_input)

        # Should remain unchanged
        assert test_message_output["messageCode"] == "T"
        assert test_message_output["pseudoMessageCode"] == "F"
        assert test_message_output["text"] == "Already a test"

    def test_does_not_mutate_original(self):
        """Converting to test message should not mutate the original dict"""
        original_message = {
            "messageCode": "F",
            "text": "Original",
        }

        test_message = convert_to_test_message(original_message)

        # Original should be unchanged
        assert original_message["messageCode"] == "F"
        assert "pseudoMessageCode" not in original_message
        
        # Test message should be modified
        assert test_message["messageCode"] == "T"
        assert test_message["pseudoMessageCode"] == "F"

    def test_preserves_all_fields(self):
        """All fields from original message should be preserved in test message"""
        complex_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": "Complex message with many fields",
            "referenceIndicator": "3",
            "referencedMessage": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "subjectCode": "10",
            "dateTime": "2025-10-13T12:00:00Z",
            "duration": "P1D",
            "objectType": "20",
            "objectLatitude": "+40.7128",
            "objectLongitude": "-074.0060",
        }

        test_message = convert_to_test_message(complex_message)

        # All original fields should be present
        assert test_message["prefix"] == "WF"
        assert test_message["version"] == "1"
        assert test_message["text"] == "Complex message with many fields"
        assert test_message["referenceIndicator"] == "3"
        assert test_message["referencedMessage"] == "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        assert test_message["subjectCode"] == "10"
        assert test_message["dateTime"] == "2025-10-13T12:00:00Z"
        
        # Plus test message fields
        assert test_message["messageCode"] == "T"
        assert test_message["pseudoMessageCode"] == "F"
