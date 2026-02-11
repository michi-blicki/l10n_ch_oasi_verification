# -*- coding: utf-8 -*-
"""
OASI (Old-Age and Survivors' Insurance) Validation Utility

This module provides validation utilities for Swiss Social Security IDs (OASI/AHV/AVS).
The OASI is a 13-digit number that always starts with 756 (Switzerland ISO 3166-1 numeric).
The last digit is a check digit calculated using ISO 7064 Mod 11,10 algorithm.

Format: 756.XXXX.XXXX.XX or 756XXXXXXXXXX
"""

import re
from odoo.exceptions import ValidationError


class OASIValidator:
    """Utility class for OASI validation"""

    COUNTRY_CODE = "756"  # Switzerland ISO 3166-1 numeric
    TOTAL_DIGITS = 13
    WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 7, 6]  # Weights for ISO 7064 Mod 11,10

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
        Calculate the check digit for OASI using ISO 7064 Mod 11,10.

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

        # Calculate sum with weights
        total = sum(int(digit) * weight for digit, weight in zip(digits, cls.WEIGHTS))

        # ISO 7064 Mod 11,10: check_digit = (11 - (sum mod 11)) mod 10
        check_digit = (11 - (total % 11)) % 10

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
