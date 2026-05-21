# -*- coding: utf-8 -*-
"""
OASI (Old-Age and Survivors' Insurance) Validation Utility

This module provides validation utilities for Swiss Social Security IDs (OASI/AHV/AVS).
The OASI is a 13-digit number that always starts with 756 (Switzerland ISO 3166-1 numeric).
The last digit is a check digit calculated using the EAN-13 algorithm (modulo 10).

Format: 756.XXXX.XXXX.XX or 756XXXXXXXXXX
"""

import re
from odoo.exceptions import ValidationError


class OASIValidator:
    """Utility class for OASI validation"""

    COUNTRY_CODE = "756"  # Switzerland ISO 3166-1 numeric
    TOTAL_DIGITS = 13
    ENV_TYPE_PRODUCTION = "production"
    ENV_TYPE_STAGING = "staging"
    ENV_TYPE_DEVELOPMENT = "development"
    TEST_RANGE_START = "7569900000000"
    TEST_RANGE_END = "7569999999999"

    @classmethod
    def sanitize(cls, oasi_string):
        """
        Remove all non-digit characters from OASI string.

        Args:
            oasi_string: String representation of OASI (with or without dots)

        Returns:
            String containing only digits
        """
        if not oasi_string:
            return ""
        return re.sub(r"\D", "", str(oasi_string).strip())

    @classmethod
    def is_valid_format(cls, oasi_string):
        """
        Validate OASI format.

        Args:
            oasi_string: String representation of OASI (with or without dots)

        Returns:
            Tuple (is_valid: bool, sanitized_oasi: str)
        """
        sanitized = cls.sanitize(oasi_string)

        # Check length
        if len(sanitized) != cls.TOTAL_DIGITS:
            return False, sanitized

        # Check if all characters are digits
        if not sanitized.isdigit():
            return False, sanitized

        # Check country code
        if not sanitized.startswith(cls.COUNTRY_CODE):
            return False, sanitized

        return True, sanitized

    @classmethod
    def calculate_check_digit(cls, oasi_string):
        """
        Calculate the check digit for OASI using EAN-13 algorithm.

        The Swiss OASI number uses the EAN-13 (modulo 10) algorithm:
        1. Assign weights alternating 1 and 3 (odd positions get 1, even get 3)
        2. Calculate sum = Σ(digit × weight) for first 12 digits
        3. Check digit = (10 - (sum % 10)) % 10

        Args:
            oasi_string: String representation of first 12 digits

        Returns:
            Integer (0-9) representing the check digit

        Raises:
            ValueError: If input is invalid
        """
        sanitized = cls.sanitize(oasi_string)

        # Take first 12 digits
        if len(sanitized) >= 12:
            digits = sanitized[:12]
        else:
            digits = sanitized

        if len(digits) != 12 or not digits.isdigit():
            raise ValueError(
                "Input must be 12 digits for check digit calculation"
            )

        # EAN-13 algorithm: alternating weights of 1 and 3
        # Position 0 (1st digit) gets weight 1, position 1 (2nd digit) gets weight 3, etc.
        total = 0
        for i, digit_char in enumerate(digits):
            weight = 3 if i % 2 == 1 else 1
            total += int(digit_char) * weight

        # Check digit calculation
        check_digit = (10 - (total % 10)) % 10

        return check_digit

    @classmethod
    def validate_check_digit(cls, oasi_string):
        """
        Validate the check digit of OASI.

        Args:
            oasi_string: String representation of complete OASI (13 digits)

        Returns:
            Tuple (is_valid: bool, calculated_check_digit: int)

        Raises:
            ValueError: If format is invalid
        """
        format_valid, sanitized = cls.is_valid_format(oasi_string)

        if not format_valid:
            raise ValueError(
                f"Invalid OASI format. Expected 13 digits starting with 756, got: {sanitized}"
            )

        # Get the provided check digit (last digit)
        provided_check_digit = int(sanitized[-1])

        # Calculate expected check digit
        calculated_check_digit = cls.calculate_check_digit(sanitized[:12])

        is_valid = provided_check_digit == calculated_check_digit

        return is_valid, calculated_check_digit

    @classmethod
    def is_valid(cls, oasi_string):
        """
        Complete OASI validation (format + check digit).

        Args:
            oasi_string: String representation of OASI (with or without dots)

        Returns:
            Boolean indicating if OASI is valid
        """
        try:
            format_valid, _ = cls.is_valid_format(oasi_string)
            if not format_valid:
                return False

            check_digit_valid, _ = cls.validate_check_digit(oasi_string)
            return check_digit_valid
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_or_raise(cls, oasi_string, field_name="OASI"):
        """
        Validate OASI and raise ValidationError if invalid.

        Args:
            oasi_string: String representation of OASI
            field_name: Name of field for error message

        Raises:
            ValidationError: If OASI is invalid
        """
        if not oasi_string:
            return  # Allow empty values (use @api.constrains for required check)

        format_valid, sanitized = cls.is_valid_format(oasi_string)

        if not format_valid:
            raise ValidationError(
                f"Invalid {field_name} format. "
                f"Expected 13 digits starting with 756, got: {sanitized}"
            )

        try:
            check_digit_valid, calculated = cls.validate_check_digit(
                sanitized
            )
            if not check_digit_valid:
                raise ValidationError(
                    f"Invalid {field_name} check digit. "
                    f"Got {sanitized[-1]}, expected {calculated} (last digit)."
                )
        except ValueError as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")

    @classmethod
    def is_test_range(cls, oasi_string):
        """
        Check if OASI is in the official Swiss test/simulation range.

        Range: 756.9900.0000.00 to 756.9999.9999.99

        Args:
            oasi_string: String representation of OASI (with or without dots)

        Returns:
            Boolean indicating if OASI is in test range
        """
        format_valid, sanitized = cls.is_valid_format(oasi_string)
        if not format_valid:
            return False

        return cls.TEST_RANGE_START <= sanitized <= cls.TEST_RANGE_END

    @classmethod
    def normalize_environment_type(cls, environment_type):
        """
        Normalize runtime environment type to one of known values.

        Unknown or empty values are treated as production for safe defaults.
        """
        normalized = (environment_type or "").strip().lower()
        if normalized in {
            cls.ENV_TYPE_PRODUCTION,
            cls.ENV_TYPE_STAGING,
            cls.ENV_TYPE_DEVELOPMENT,
        }:
            return normalized
        return cls.ENV_TYPE_PRODUCTION

    @classmethod
    def is_non_production_environment_type(cls, environment_type):
        """Return True for staging/development environment types."""
        normalized = cls.normalize_environment_type(environment_type)
        return normalized in {
            cls.ENV_TYPE_STAGING,
            cls.ENV_TYPE_DEVELOPMENT,
        }
