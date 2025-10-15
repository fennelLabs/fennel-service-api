"""
Test script to debug Test message creation for Infrastructure (I) and Free Text (F) 
messages that reference previous I messages.

This script tests:
1. Sending an Infrastructure (I) message as a Test (T) message
2. Sending a Free Text (F) message as a Test (T) message that references the I message
"""

def test_infrastructure_test_message():
    """Test converting Infrastructure message to Test message"""
    print("\n" + "="*80)
    print("TEST 1: Infrastructure (I) Message as Test (T) Message")
    print("="*80)
    
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
    
    print("\nOriginal Infrastructure message:")
    for key, value in infrastructure_message.items():
        print(f"  {key}: {value}")
    
    # Convert to test message
    test_message = convert_to_test_message(infrastructure_message)
    
    print("\nConverted to Test message:")
    for key, value in test_message.items():
        print(f"  {key}: {value}")
    
    # Encode the test message
    encoded, success = whiteflag_encoder_helper(test_message)
    
    print(f"\nEncoding success: {success}")
    if success:
        print(f"Encoded message: {encoded}")
    else:
        print(f"Encoding failed: {encoded}")
    
    return test_message, encoded, success


def test_free_text_referencing_infrastructure():
    """Test Free Text message referencing an Infrastructure message"""
    print("\n" + "="*80)
    print("TEST 2: Free Text (F) Message Referencing Infrastructure Message")
    print("="*80)
    
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
    
    print("\nOriginal Free Text message (referencing infrastructure):")
    for key, value in free_text_message.items():
        print(f"  {key}: {value}")
    
    # Convert to test message
    test_message = convert_to_test_message(free_text_message)
    
    print("\nConverted to Test message:")
    for key, value in test_message.items():
        print(f"  {key}: {value}")
    
    # Encode the test message
    encoded, success = whiteflag_encoder_helper(test_message)
    
    print(f"\nEncoding success: {success}")
    if success:
        print(f"Encoded message: {encoded}")
    else:
        print(f"Encoding failed: {encoded}")
    
    return test_message, encoded, success


def test_free_text_without_reference():
    """Test Free Text message without reference"""
    print("\n" + "="*80)
    print("TEST 3: Free Text (F) Message Without Reference")
    print("="*80)
    
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
    
    print("\nOriginal Free Text message (no reference):")
    for key, value in free_text_message.items():
        print(f"  {key}: {value}")
    
    # Convert to test message
    test_message = convert_to_test_message(free_text_message)
    
    print("\nConverted to Test message:")
    for key, value in test_message.items():
        print(f"  {key}: {value}")
    
    # Encode the test message
    encoded, success = whiteflag_encoder_helper(test_message)
    
    print(f"\nEncoding success: {success}")
    if success:
        print(f"Encoded message: {encoded}")
    else:
        print(f"Encoding failed: {encoded}")
    
    return test_message, encoded, success


if __name__ == "__main__":
    import os
    import sys
    import django
    
    # Setup Django
    sys.path.insert(0, os.path.dirname(__file__))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fennelserver.settings')
    django.setup()
    
    # Import after Django setup
    from main.whiteflag_helpers import convert_to_test_message, whiteflag_encoder_helper
    
    print("\n" + "#"*80)
    print("# Testing Test Message Creation with References")
    print("#"*80)
    
    # Run tests
    try:
        test1_msg, test1_encoded, test1_success = test_infrastructure_test_message()
        test2_msg, test2_encoded, test2_success = test_free_text_referencing_infrastructure()
        test3_msg, test3_encoded, test3_success = test_free_text_without_reference()
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Test 1 (Infrastructure as Test): {'✓ PASSED' if test1_success else '✗ FAILED'}")
        print(f"Test 2 (Free Text with Reference): {'✓ PASSED' if test2_success else '✗ FAILED'}")
        print(f"Test 3 (Free Text without Reference): {'✓ PASSED' if test3_success else '✗ FAILED'}")
        
        if not all([test1_success, test2_success, test3_success]):
            print("\n⚠️  Some tests failed. Check the error messages above.")
            sys.exit(1)
        else:
            print("\n✓ All tests passed!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
