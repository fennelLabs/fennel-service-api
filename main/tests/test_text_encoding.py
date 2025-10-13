"""
Test WhiteFlag text field encoding/decoding for A, R, and F messages
Tests that UTF-8 text fields are properly handled by the Rust encoder/decoder.
The Rust WhiteFlag library handles UTF-8 encoding automatically - we should NOT
manually hex-encode text fields in Python.
"""
from django.test import TestCase
from main.whiteflag_helpers import whiteflag_encoder_helper, decode


class TestTextFieldEncoding(TestCase):
    """Test that text fields in A, R, and F messages are properly encoded/decoded as UTF-8"""

    def test_free_text_message_encoding(self):
        """Test Free Text (F) message with UTF-8 text field"""
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": "Hello, World! 🌍",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        
        # Encode the message
        encoded_message, encode_success = whiteflag_encoder_helper(message)
        self.assertTrue(encode_success, "Free Text message should encode successfully")
        self.assertIsNotNone(encoded_message)
        
        # Decode the message
        decoded_message, decode_success = decode(encoded_message)
        self.assertTrue(decode_success, "Free Text message should decode successfully")
        self.assertIsNotNone(decoded_message)
        
        # Check that text is properly decoded as UTF-8
        self.assertEqual(
            decoded_message.get("text"),
            "Hello, World! 🌍",
            "Text field should be decoded as UTF-8 string"
        )

    def test_authentication_message_encoding(self):
        """Test Authentication (A) message with UTF-8 verificationData field"""
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            "verificationMethod": "1",
            "verificationData": "https://example.org/whiteflag/verification",
        }
        
        # Encode the message
        encoded_message, encode_success = whiteflag_encoder_helper(message)
        self.assertTrue(encode_success, "Authentication message should encode successfully")
        self.assertIsNotNone(encoded_message)
        
        # Decode the message
        decoded_message, decode_success = decode(encoded_message)
        self.assertTrue(decode_success, "Authentication message should decode successfully")
        self.assertIsNotNone(decoded_message)
        
        # Check that verificationData is properly decoded as UTF-8
        self.assertEqual(
            decoded_message.get("verificationData"),
            "https://example.org/whiteflag/verification",
            "verificationData field should be decoded as UTF-8 string"
        )

    def test_resource_message_encoding(self):
        """Test Resource (R) message with UTF-8 resourceData field"""
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "R",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            "resourceMethod": "1",
            "resourceData": "Medical supplies: 100 bandages, 50 syringes",
        }
        
        # Encode the message
        encoded_message, encode_success = whiteflag_encoder_helper(message)
        self.assertTrue(encode_success, "Resource message should encode successfully")
        self.assertIsNotNone(encoded_message)
        
        # Decode the message
        decoded_message, decode_success = decode(encoded_message)
        self.assertTrue(decode_success, "Resource message should decode successfully")
        self.assertIsNotNone(decoded_message)
        
        # Check that resourceData is properly decoded as UTF-8
        self.assertEqual(
            decoded_message.get("resourceData"),
            "Medical supplies: 100 bandages, 50 syringes",
            "resourceData field should be decoded as UTF-8 string"
        )

    def test_json_string_in_text_field(self):
        """Test that JSON strings in text field are properly handled"""
        json_text = '{"name":"University of Pennsylvania","text":"Leges sine moribus vanae"}'
        message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "text": json_text,
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        
        # Encode the message
        encoded_message, encode_success = whiteflag_encoder_helper(message)
        self.assertTrue(encode_success, "Message with JSON text should encode")
        
        # Decode the message
        decoded_message, decode_success = decode(encoded_message)
        self.assertTrue(decode_success, "Message with JSON text should decode")
        
        # Check that JSON string is preserved
        self.assertEqual(
            decoded_message.get("text"),
            json_text,
            "JSON string in text field should be preserved"
        )
