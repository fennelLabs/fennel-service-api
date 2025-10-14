"""
Test UTF-8 encoding for Test (T) messages with pseudoMessageCode "F"

This test verifies that Test messages properly encode UTF-8 text when testing
Free Text message functionality. Test messages allow flexible testing without
reference validation errors.

NOTE: These tests require the Rust encoder service to be running.
They will be skipped if the service is not available.
"""

from django.test import TestCase
from main.whiteflag_helpers import whiteflag_encoder_helper, decode
import requests


class TestMessageEncoding(TestCase):
    """Test that Test (T) messages with pseudoMessageCode F properly encode UTF-8"""

    def test_test_message_with_free_text(self):
        """
        Test message (T) with pseudoMessageCode F should encode and decode UTF-8 text correctly
        
        Test messages are designed for testing on live chains without polluting
        operational data. They have the same fields as the message type being tested.
        """
        # Create a Test message testing Free Text functionality
        test_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",  # Test message type
            "pseudoMessageCode": "F",  # Testing Free Text functionality
            "text": "Testing UTF-8: Café ☕",  # Same text field as Free Text
            "referenceIndicator": "0",  # Test messages can use any reference
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        # Encode the message
        encoded, success = whiteflag_encoder_helper(test_message)
        assert success, "Encoding should succeed"
        assert isinstance(encoded, str), "Encoded message should be a string"

        # Decode the message
        decoded, success = decode(encoded)
        assert success, "Decoding should succeed"
        
        # Verify the decoded message has correct fields
        assert decoded["messageCode"] == "T", "Should be Test message type"
        assert decoded["pseudoMessageCode"] == "F", "Should indicate Free Text testing"
        
        # Critical: text should be decoded as UTF-8 string, NOT hex
        assert decoded["text"] == "Testing UTF-8: Café ☕", (
            "Text should be decoded as UTF-8 string, not hex. "
            f"Expected 'Testing UTF-8: Café ☕', got '{decoded['text']}'"
        )

    def test_test_message_with_json_string(self):
        """
        Test message with JSON string in text field (schoolpilot use case)
        """
        json_text = '{"school_id":"school_001","status":"active"}'
        
        test_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",
            "pseudoMessageCode": "F",
            "text": json_text,
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        # Encode and decode
        encoded, success = whiteflag_encoder_helper(test_message)
        assert success, "Encoding should succeed"

        decoded, success = decode(encoded)
        assert success, "Decoding should succeed"

        # Verify JSON string is preserved
        assert decoded["text"] == json_text, (
            f"JSON string should be preserved. Expected '{json_text}', got '{decoded['text']}'"
        )

    def test_test_message_with_emoji(self):
        """
        Test message with emoji characters
        """
        test_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",
            "pseudoMessageCode": "F",
            "text": "🌍 Testing UTF-8 ✓",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        # Encode and decode
        encoded, success = whiteflag_encoder_helper(test_message)
        assert success, "Encoding should succeed"

        decoded, success = decode(encoded)
        assert success, "Decoding should succeed"

        # Verify emoji is preserved
        assert decoded["text"] == "🌍 Testing UTF-8 ✓", (
            f"Emoji should be preserved. Expected '🌍 Testing UTF-8 ✓', got '{decoded['text']}'"
        )

    def test_test_message_clearly_marked(self):
        """
        Verify Test messages are clearly marked and distinguishable from real data
        """
        test_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",  # This is the key identifier
            "pseudoMessageCode": "F",
            "text": "This is test data, not operational",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        # Encode and decode
        encoded, success = whiteflag_encoder_helper(test_message)
        assert success, "Encoding should succeed"

        decoded, success = decode(encoded)
        assert success, "Decoding should succeed"

        # Verify it's clearly marked as test data
        assert decoded["messageCode"] == "T", (
            "Test messages must be marked with messageCode 'T' to distinguish from real data"
        )

    def test_comparison_free_text_vs_test_message(self):
        """
        Compare Free Text (F) and Test (T with pseudoMessageCode F) messages
        to verify they encode text fields identically
        """
        test_text = "UTF-8 encoding test"
        
        # Regular Free Text message
        free_text_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": test_text,
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        
        # Test message testing Free Text
        test_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "T",
            "pseudoMessageCode": "F",
            "text": test_text,
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }

        # Encode both
        encoded_f, success_f = whiteflag_encoder_helper(free_text_message)
        assert success_f, "Free Text encoding should succeed"
        
        encoded_t, success_t = whiteflag_encoder_helper(test_message)
        assert success_t, "Test message encoding should succeed"

        # Decode both
        decoded_f, success_f = decode(encoded_f)
        assert success_f, "Free Text decoding should succeed"
        
        decoded_t, success_t = decode(encoded_t)
        assert success_t, "Test message decoding should succeed"

        # Both should have the same text field content
        assert decoded_f["text"] == test_text, "Free Text should preserve UTF-8"
        assert decoded_t["text"] == test_text, "Test message should preserve UTF-8"
        assert decoded_f["text"] == decoded_t["text"], (
            "Both message types should encode text identically"
        )
        
        # But messageCode should be different
        assert decoded_f["messageCode"] == "F", "Should be Free Text"
        assert decoded_t["messageCode"] == "T", "Should be Test message"
