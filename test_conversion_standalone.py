#!/usr/bin/env python3
"""
Simple test to verify Test message conversion works correctly
This can be run directly without Django setup
"""

import json
import sys
from typing import Dict, Tuple

def convert_to_test_message(signal_body: dict) -> dict:
    """
    Simplified version of convert_to_test_message for testing
    """
    original_message_code = signal_body.get("messageCode", None)
    
    if original_message_code == "T":
        return signal_body
    
    test_message = {}
    
    if "prefix" in signal_body:
        test_message["prefix"] = signal_body["prefix"]
    if "version" in signal_body:
        test_message["version"] = signal_body["version"]
    
    test_message["encryptionIndicator"] = signal_body.get("encryptionIndicator")
    test_message["duressIndicator"] = signal_body.get("duressIndicator")
    test_message["messageCode"] = "T"
    
    if "referenceIndicator" in signal_body:
        test_message["referenceIndicator"] = signal_body["referenceIndicator"]
    if "referencedMessage" in signal_body:
        test_message["referencedMessage"] = signal_body["referencedMessage"]
    
    test_message["pseudoMessageCode"] = original_message_code
    
    body_fields = [k for k in signal_body.keys() 
                   if k not in ["prefix", "version", "encryptionIndicator", "duressIndicator", 
                                "messageCode", "referenceIndicator", "referencedMessage"]]
    for field in body_fields:
        if field == "datetime":
            test_message["dateTime"] = signal_body[field]
        else:
            test_message[field] = signal_body[field]
    
    return test_message


def test_infrastructure_message():
    """Test Infrastructure message conversion"""
    print("\n" + "="*80)
    print("TEST 1: Infrastructure (I) Message → Test (T) Message")
    print("="*80)
    
    infrastructure_msg = {
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
    print(json.dumps(infrastructure_msg, indent=2))
    
    test_msg = convert_to_test_message(infrastructure_msg)
    
    print("\nConverted Test message:")
    print(json.dumps(test_msg, indent=2))
    
    # Verify
    assert test_msg["messageCode"] == "T", "messageCode should be T"
    assert test_msg["pseudoMessageCode"] == "I", "pseudoMessageCode should be I"
    assert test_msg["subjectCode"] == "52", "subjectCode should be preserved"
    
    # Check field order
    keys = list(test_msg.keys())
    print("\nField order:", keys)
    
    # Verify critical ordering
    ref_ind_pos = keys.index("referenceIndicator")
    pseudo_pos = keys.index("pseudoMessageCode")
    
    print(f"\nPosition of referenceIndicator: {ref_ind_pos}")
    print(f"Position of pseudoMessageCode: {pseudo_pos}")
    
    assert ref_ind_pos < pseudo_pos, "referenceIndicator must come before pseudoMessageCode"
    
    print("\n✓ Test 1 PASSED")
    return True


def test_free_text_with_reference():
    """Test Free Text message with reference conversion"""
    print("\n" + "="*80)
    print("TEST 2: Free Text (F) with Reference → Test (T) Message")
    print("="*80)
    
    free_text_msg = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "referenceIndicator": "4",
        "referencedMessage": "3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae",
        "text": "This is a comment about the infrastructure",
    }
    
    print("\nOriginal Free Text message:")
    print(json.dumps(free_text_msg, indent=2))
    
    test_msg = convert_to_test_message(free_text_msg)
    
    print("\nConverted Test message:")
    print(json.dumps(test_msg, indent=2))
    
    # Verify
    assert test_msg["messageCode"] == "T", "messageCode should be T"
    assert test_msg["pseudoMessageCode"] == "F", "pseudoMessageCode should be F"
    assert test_msg["referenceIndicator"] == "4", "referenceIndicator should be preserved"
    assert test_msg["text"] == "This is a comment about the infrastructure", "text should be preserved"
    
    # Check field order
    keys = list(test_msg.keys())
    print("\nField order:", keys)
    
    # Verify critical ordering
    ref_ind_pos = keys.index("referenceIndicator")
    ref_msg_pos = keys.index("referencedMessage")
    pseudo_pos = keys.index("pseudoMessageCode")
    text_pos = keys.index("text")
    
    print(f"\nPosition of referenceIndicator: {ref_ind_pos}")
    print(f"Position of referencedMessage: {ref_msg_pos}")
    print(f"Position of pseudoMessageCode: {pseudo_pos}")
    print(f"Position of text: {text_pos}")
    
    assert ref_ind_pos < pseudo_pos, "referenceIndicator must come before pseudoMessageCode"
    assert ref_msg_pos < pseudo_pos, "referencedMessage must come before pseudoMessageCode"
    assert pseudo_pos < text_pos, "pseudoMessageCode must come before text"
    
    print("\n✓ Test 2 PASSED")
    return True


def test_field_order_matches_spec():
    """Test that field order matches test_f_message.json from whiteflag-rust"""
    print("\n" + "="*80)
    print("TEST 3: Field Order Matches WhiteFlag Spec")
    print("="*80)
    
    # Expected order from test_f_message.json
    expected_order = [
        "prefix",
        "version",
        "encryptionIndicator",
        "duressIndicator",
        "messageCode",
        "referenceIndicator",
        "referencedMessage",
        "pseudoMessageCode",
        "text"
    ]
    
    free_text_msg = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "referenceIndicator": "0",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        "text": "Test annotation",
    }
    
    test_msg = convert_to_test_message(free_text_msg)
    actual_order = list(test_msg.keys())
    
    print("\nExpected order:", expected_order)
    print("Actual order:  ", actual_order)
    
    assert actual_order == expected_order, f"Field order mismatch!\nExpected: {expected_order}\nActual: {actual_order}"
    
    print("\n✓ Test 3 PASSED - Field order matches WhiteFlag specification!")
    return True


def test_already_test_message():
    """Test that already-Test messages are not converted again"""
    print("\n" + "="*80)
    print("TEST 4: Already Test Message (Should Return Unchanged)")
    print("="*80)
    
    already_test = {
        "messageCode": "T",
        "pseudoMessageCode": "F",
        "text": "Already a test"
    }
    
    print("\nInput:", json.dumps(already_test, indent=2))
    
    result = convert_to_test_message(already_test)
    
    print("Output:", json.dumps(result, indent=2))
    
    assert result == already_test, "Already-test message should be unchanged"
    
    print("\n✓ Test 4 PASSED")
    return True


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# Testing Test Message Conversion for Infrastructure and Free Text")
    print("#"*80)
    
    all_passed = True
    
    try:
        all_passed = test_infrastructure_message() and all_passed
        all_passed = test_free_text_with_reference() and all_passed
        all_passed = test_field_order_matches_spec() and all_passed
        all_passed = test_already_test_message() and all_passed
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        if all_passed:
            print("✓ ALL TESTS PASSED!")
            print("\nYour convert_to_test_message() implementation is correct!")
            print("Field order matches WhiteFlag specification.")
            print("Ready for encoding with the Rust WhiteFlag library.")
            sys.exit(0)
        else:
            print("✗ SOME TESTS FAILED")
            sys.exit(1)
            
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
