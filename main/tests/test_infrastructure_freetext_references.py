"""
Test script to debug Test message creation for Infrastructure (I) and Free Text (F) 
messages that reference previous I messages.
"""

from django.test import TestCase
from main.whiteflag_helpers import convert_to_test_message, whiteflag_encoder_helper, decode


class TestInfrastructureAndFreeTextReferences(TestCase):
    """Test Infrastructure and Free Text messages with references as Test messages"""

    def test_infrastructure_as_test_message(self):
        """Test converting Infrastructure (I) message to Test (T) message"""
        infrastructure_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "I",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            "subjectCode": "52",
            "dateTime": "2023-09-01T09:37:09Z",
            "duration": "P00D00H00M",
            "objectType": "22",
            "objectLatitude": "+39.09144",
            "objectLongitude": "-120.03830",
            "objectSizeDim1": "0000",
            "objectSizeDim2": "0000",
            "objectOrientation": "000",
        }
        
        print("\n" + "="*80)
        print("TEST: Infrastructure (I) Message as Test (T) Message")
        print("="*80)
        print("\nOriginal Infrastructure message:")
        for key, value in infrastructure_message.items():
            print(f"  {key}: {value}")
        
        # Convert to test message
        test_message = convert_to_test_message(infrastructure_message)
        
        print("\nConverted to Test message:")
        for key, value in test_message.items():
            print(f"  {key}: {value}")
        
        # Verify structure
        assert test_message["messageCode"] == "T", "Should be Test message"
        assert test_message["pseudoMessageCode"] == "I", "Should indicate Infrastructure testing"
        
        # Encode the test message
        encoded, success = whiteflag_encoder_helper(test_message)
        
        print(f"\nEncoding success: {success}")
        if success:
            print(f"Encoded message: {encoded}")
            
            # Try to decode it back
            decoded, decode_success = decode(encoded)
            if decode_success:
                print(f"\nDecoded message:")
                for key, value in decoded.items():
                    print(f"  {key}: {value}")
                assert decoded["messageCode"] == "T"
                assert decoded["pseudoMessageCode"] == "I"
            else:
                print(f"Decoding failed: {decoded}")
        else:
            print(f"Encoding failed: {encoded}")
        
        assert success, f"Encoding should succeed but got: {encoded}"

    def test_free_text_referencing_infrastructure(self):
        """Test Free Text (F) message referencing an Infrastructure message as Test"""
        # Simulate a previous infrastructure message with a transaction hash
        previous_tx_hash = "3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae"
        
        free_text_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "referenceIndicator": "4",  # References another message
            "referencedMessage": previous_tx_hash,
            "text": "This is a comment about the infrastructure",
        }
        
        print("\n" + "="*80)
        print("TEST: Free Text (F) Message Referencing Infrastructure Message")
        print("="*80)
        print("\nOriginal Free Text message (referencing infrastructure):")
        for key, value in free_text_message.items():
            print(f"  {key}: {value}")
        
        # Convert to test message
        test_message = convert_to_test_message(free_text_message)
        
        print("\nConverted to Test message:")
        for key, value in test_message.items():
            print(f"  {key}: {value}")
        
        # Verify structure - check the order of keys
        keys_list = list(test_message.keys())
        print(f"\nField order: {keys_list}")
        
        # According to WhiteFlag spec and test_f_message.json, the order should be:
        # 1. prefix, version, encryptionIndicator, duressIndicator, messageCode
        # 2. referenceIndicator, referencedMessage
        # 3. pseudoMessageCode
        # 4. text (body fields)
        
        # Find positions
        ref_indicator_pos = keys_list.index("referenceIndicator") if "referenceIndicator" in keys_list else -1
        ref_message_pos = keys_list.index("referencedMessage") if "referencedMessage" in keys_list else -1
        pseudo_code_pos = keys_list.index("pseudoMessageCode") if "pseudoMessageCode" in keys_list else -1
        text_pos = keys_list.index("text") if "text" in keys_list else -1
        
        print(f"\nPosition of referenceIndicator: {ref_indicator_pos}")
        print(f"Position of referencedMessage: {ref_message_pos}")
        print(f"Position of pseudoMessageCode: {pseudo_code_pos}")
        print(f"Position of text: {text_pos}")
        
        # Reference fields should come BEFORE pseudoMessageCode
        if ref_indicator_pos != -1 and pseudo_code_pos != -1:
            assert ref_indicator_pos < pseudo_code_pos, \
                f"referenceIndicator (pos {ref_indicator_pos}) should come before pseudoMessageCode (pos {pseudo_code_pos})"
        
        if ref_message_pos != -1 and pseudo_code_pos != -1:
            assert ref_message_pos < pseudo_code_pos, \
                f"referencedMessage (pos {ref_message_pos}) should come before pseudoMessageCode (pos {pseudo_code_pos})"
        
        # pseudoMessageCode should come BEFORE text
        if pseudo_code_pos != -1 and text_pos != -1:
            assert pseudo_code_pos < text_pos, \
                f"pseudoMessageCode (pos {pseudo_code_pos}) should come before text (pos {text_pos})"
        
        # Verify content
        assert test_message["messageCode"] == "T", "Should be Test message"
        assert test_message["pseudoMessageCode"] == "F", "Should indicate Free Text testing"
        assert test_message["referenceIndicator"] == "4", "Should preserve reference indicator"
        assert test_message["referencedMessage"] == previous_tx_hash, "Should preserve referenced message"
        
        # Encode the test message
        encoded, success = whiteflag_encoder_helper(test_message)
        
        print(f"\nEncoding success: {success}")
        if success:
            print(f"Encoded message: {encoded}")
            
            # Try to decode it back
            decoded, decode_success = decode(encoded)
            if decode_success:
                print(f"\nDecoded message:")
                for key, value in decoded.items():
                    print(f"  {key}: {value}")
                assert decoded["messageCode"] == "T"
                assert decoded["pseudoMessageCode"] == "F"
                assert decoded["referenceIndicator"] == "4"
            else:
                print(f"Decoding failed: {decoded}")
        else:
            print(f"Encoding failed: {encoded}")
        
        assert success, f"Encoding should succeed but got: {encoded}"

    def test_free_text_without_reference(self):
        """Test Free Text message without reference as Test message"""
        free_text_message = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "F",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            "text": "This is a standalone free text message",
        }
        
        print("\n" + "="*80)
        print("TEST: Free Text (F) Message Without Reference")
        print("="*80)
        print("\nOriginal Free Text message (no reference):")
        for key, value in free_text_message.items():
            print(f"  {key}: {value}")
        
        # Convert to test message
        test_message = convert_to_test_message(free_text_message)
        
        print("\nConverted to Test message:")
        for key, value in test_message.items():
            print(f"  {key}: {value}")
        
        # Verify structure
        assert test_message["messageCode"] == "T", "Should be Test message"
        assert test_message["pseudoMessageCode"] == "F", "Should indicate Free Text testing"
        
        # Encode the test message
        encoded, success = whiteflag_encoder_helper(test_message)
        
        print(f"\nEncoding success: {success}")
        if success:
            print(f"Encoded message: {encoded}")
            
            # Try to decode it back
            decoded, decode_success = decode(encoded)
            if decode_success:
                print(f"\nDecoded message:")
                for key, value in decoded.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Decoding failed: {decoded}")
        else:
            print(f"Encoding failed: {encoded}")
        
        assert success, f"Encoding should succeed but got: {encoded}"
