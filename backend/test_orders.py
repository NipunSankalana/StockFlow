import pytest
from decimal import Decimal
from routes.orders import parse_service_fee

def test_parse_service_fee_valid_cases():
    assert parse_service_fee("10.50") == Decimal("10.50")
    assert parse_service_fee(10) == Decimal("10.00")
    assert parse_service_fee(10.5) == Decimal("10.50")
    assert parse_service_fee(Decimal("10.50")) == Decimal("10.50")
    assert parse_service_fee("  10.50  ") == Decimal("10.50")
    assert parse_service_fee("0") == Decimal("0.00")

def test_parse_service_fee_invalid_cases():
    assert parse_service_fee(None) is None
    assert parse_service_fee("abc") is None
    assert parse_service_fee("") is None
    assert parse_service_fee(" ") is None
    assert parse_service_fee([]) is None
    assert parse_service_fee({}) is None

def test_parse_service_fee_negative_numbers():
    assert parse_service_fee("-10.50") is None
    assert parse_service_fee(-10) is None
    assert parse_service_fee(Decimal("-10.50")) is None

def test_parse_service_fee_infinity_nan():
    assert parse_service_fee("Infinity") is None
    assert parse_service_fee("-Infinity") is None
    assert parse_service_fee("NaN") is None
    assert parse_service_fee(Decimal("Infinity")) is None
    assert parse_service_fee(Decimal("NaN")) is None

def test_parse_service_fee_large_numbers():
    # MAX_SERVICE_FEE is Decimal('99999999.99')
    assert parse_service_fee("99999999.99") == Decimal("99999999.99")
    assert parse_service_fee("100000000.00") is None
    assert parse_service_fee("999999999.99") is None
