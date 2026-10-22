import time
from unittest.mock import patch
import pytest

# Adjust imports based on the actual module name and path in the project
from otp_service import generate_otp, verify_otp, clear_otp, OTP_EXPIRY_SECONDS, _otp_store, _make_key

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup: clear the store before each test
    _otp_store.clear()
    yield
    # Teardown: clear the store after each test
    _otp_store.clear()

def test_verify_otp_success():
    email = "test@example.com"
    purpose = "register"
    code = generate_otp(email, purpose)

    is_valid, msg = verify_otp(email, code, purpose)

    assert is_valid is True
    assert msg == "OTP verified successfully."

    # Ensure it's invalidated after success
    key = _make_key(email, purpose)
    assert key not in _otp_store

def test_verify_otp_not_requested():
    email = "notrequested@example.com"
    purpose = "register"
    code = "123456"

    is_valid, msg = verify_otp(email, code, purpose)

    assert is_valid is False
    assert msg == "OTP has expired or was not requested. Please request a new code."

def test_verify_otp_invalid_code():
    email = "test_invalid@example.com"
    purpose = "register"
    code = generate_otp(email, purpose)

    # Ensure generated code is different from what we check
    wrong_code = "000000" if code != "000000" else "111111"

    is_valid, msg = verify_otp(email, wrong_code, purpose)

    assert is_valid is False
    assert msg == "Invalid OTP code. Please check and try again."

    # Ensure the key is still in store, attempts incremented
    key = _make_key(email, purpose)
    assert key in _otp_store
    assert _otp_store[key]["attempts"] == 1

@patch('otp_service.time.time')
def test_verify_otp_expired(mock_time):
    # Set a fixed initial time
    initial_time = 1000.0
    mock_time.return_value = initial_time

    email = "test_expired@example.com"
    purpose = "register"
    code = generate_otp(email, purpose)

    # Simulate time passing beyond expiration
    mock_time.return_value = initial_time + OTP_EXPIRY_SECONDS + 1

    is_valid, msg = verify_otp(email, code, purpose)

    assert is_valid is False
    assert msg == "OTP has expired. Please request a new code."

    # Ensure it's invalidated
    key = _make_key(email, purpose)
    assert key not in _otp_store

def test_verify_otp_max_attempts():
    email = "test_attempts@example.com"
    purpose = "register"
    code = generate_otp(email, purpose)

    wrong_code = "000000" if code != "000000" else "111111"

    # 5 wrong attempts
    for _ in range(5):
        is_valid, msg = verify_otp(email, wrong_code, purpose)
        assert is_valid is False
        assert msg == "Invalid OTP code. Please check and try again."

    # 6th wrong attempt
    is_valid, msg = verify_otp(email, wrong_code, purpose)

    assert is_valid is False
    assert msg == "Too many failed attempts. Please request a new OTP."

    # Ensure it's invalidated
    key = _make_key(email, purpose)
    assert key not in _otp_store

def test_verify_otp_max_attempts_then_correct():
    email = "test_attempts_correct@example.com"
    purpose = "register"
    code = generate_otp(email, purpose)

    wrong_code = "000000" if code != "000000" else "111111"

    # 5 wrong attempts
    for _ in range(5):
        is_valid, msg = verify_otp(email, wrong_code, purpose)
        assert is_valid is False

    # 6th attempt but correct code. But the attempts check happens before code check.
    # Actually looking at the logic:
    # record["attempts"] += 1
    # if record["attempts"] > 5: return False, "Too many failed attempts..."
    # So the 6th attempt, even if correct, will fail because attempts became 6 > 5.

    is_valid, msg = verify_otp(email, code, purpose)

    assert is_valid is False
    assert msg == "Too many failed attempts. Please request a new OTP."
