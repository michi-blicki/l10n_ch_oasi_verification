# -*- coding: utf-8 -*-
"""
OASI Validation Mixin

This mixin provides OASI validation functionality that can be added to any model.
It automatically validates OASI fields using the ISO 7064 Mod 11,10 algorithm.

Usage example:
    class HrEmployee(models.Model):
        _name = 'hr.employee'
        _inherit = ['hr.employee', 'oasi.validation.mixin']

        oasi = fields.Char(string='OASI', help='Swiss Social Security ID')

        @api.constrains('oasi')
        def _validate_oasi(self):
            self._validate_oasi_field('oasi')

Or with ssnid field:
    @api.constrains('ssnid')
    def _validate_ssnid(self):
        self._validate_oasi_field('ssnid', field_label='SSNID')
"""

from odoo import api, models
from odoo.exceptions import ValidationError
from .oasi_validator import OASIValidator


class OASIValidationMixin(models.AbstractModel):
    """Mixin to add OASI validation to models"""

    _name = "oasi.validation.mixin"
    _description = "OASI Validation Mixin"

    def _validate_oasi_field(self, field_name, field_label=None):
        """
        Validate OASI in a specific field using constraints.

        Args:
            field_name: Name of the field containing OASI (e.g., 'oasi', 'ssnid')
            field_label: Display label for error messages (defaults to field_name)

        Raises:
            ValidationError: If OASI validation fails

        Example:
            @api.constrains('oasi')
            def _validate_oasi(self):
                self._validate_oasi_field('oasi')
        """
        if not field_label:
            field_label = field_name.upper()

        for record in self:
            oasi_value = getattr(record, field_name, None)
            if oasi_value:
                OASIValidator.validate_or_raise(oasi_value, field_name=field_label)

    def get_formatted_oasi(self, field_name, format_with_dots=True):
        """
        Get formatted OASI from a field.

        Args:
            field_name: Name of the field containing OASI
            format_with_dots: If True, return as 756.XXXX.XXXX.XX, else 756XXXXXXXXXX

        Returns:
            Formatted OASI string or empty string if not set

        Example:
            formatted = record.get_formatted_oasi('oasi')  # Returns "756.XXXX.XXXX.XX"
        """
        oasi_value = getattr(self, field_name, None)
        if not oasi_value:
            return ""

        sanitized = OASIValidator.sanitize(oasi_value)

        if format_with_dots:
            return f"{sanitized[0:3]}.{sanitized[3:7]}.{sanitized[7:11]}.{sanitized[11:13]}"
        else:
            return sanitized

    def is_oasi_valid(self, field_name):
        """
        Check if OASI in a field is valid.

        Args:
            field_name: Name of the field containing OASI

        Returns:
            Boolean indicating if OASI is valid

        Example:
            if record.is_oasi_valid('oasi'):
                print("Valid OASI")
        """
        oasi_value = getattr(self, field_name, None)
        return OASIValidator.is_valid(oasi_value)

    def _onchange_validate_oasi_field(self, field_name, field_label=None):
        """
        Validate OASI on field change (real-time user feedback).
        
        Returns a warning dictionary if invalid, or None if valid.
        Use in @api.onchange decorator for immediate feedback.

        Args:
            field_name: Name of the field containing OASI
            field_label: Display label for error messages (defaults to field_name)

        Returns:
            Dictionary with warning info or None if valid

        Example:
            @api.onchange('oasi_field')
            def _onchange_oasi_field(self):
                return self._onchange_validate_oasi_field('oasi_field')
        """
        if not field_label:
            field_label = field_name.upper()

        oasi_value = getattr(self, field_name, None)
        
        if not oasi_value:
            return None  # Allow empty values on change
        
        if not OASIValidator.is_valid(oasi_value):
            # Get validation error details
            format_valid, sanitized = OASIValidator.is_valid_format(oasi_value)
            
            if not format_valid:
                error_msg = (
                    f"Invalid {field_label} format. "
                    f"Expected 13 digits starting with 756, got: {sanitized}"
                )
            else:
                try:
                    check_digit_valid, calculated = OASIValidator.validate_check_digit(
                        sanitized
                    )
                    error_msg = (
                        f"Invalid {field_label} check digit. "
                        f"Got {sanitized[-1]}, expected {calculated}."
                    )
                except ValueError:
                    error_msg = f"Invalid {field_label} format."
            
            return {
                'warning': {
                    'title': f'Invalid {field_label}',
                    'message': error_msg,
                }
            }
        
        return None  # Valid OASI
