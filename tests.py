# -*- coding: utf-8 -*-
"""
Test and Example Cases for OASI Validation

This file demonstrates how to use the OASI validation utilities and includes
test cases that can be used for validation.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from ..models.oasi_validator import OASIValidator


class TestOASIValidator(TransactionCase):
    """Test cases for OASIValidator utility"""

    def test_sanitize(self):
        """Test OASI sanitization (removing non-digits)"""
        self.assertEqual(OASIValidator.sanitize("756.1234.5678.97"), "7561234567897")
        self.assertEqual(OASIValidator.sanitize("7561234567897"), "7561234567897")
        self.assertEqual(OASIValidator.sanitize("756-1234-5678-97"), "7561234567897")
        self.assertEqual(OASIValidator.sanitize(""), "")
        self.assertEqual(OASIValidator.sanitize(None), "")

    def test_format_validation_valid(self):
        """Test format validation for valid OASI"""
        is_valid, sanitized = OASIValidator.is_valid_format("756.1234.5678.97")
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, "7561234567897")

        is_valid, sanitized = OASIValidator.is_valid_format("7561234567897")
        self.assertTrue(is_valid)
        self.assertEqual(sanitized, "7561234567897")

    def test_format_validation_invalid_country_code(self):
        """Test format validation fails with wrong country code"""
        is_valid, sanitized = OASIValidator.is_valid_format("123.1234.5678.97")
        self.assertFalse(is_valid)

    def test_format_validation_invalid_length(self):
        """Test format validation fails with wrong length"""
        is_valid, sanitized = OASIValidator.is_valid_format("756.1234.567.97")  # 12 digits
        self.assertFalse(is_valid)

        is_valid, sanitized = OASIValidator.is_valid_format("756.1234.5678.970")  # 14 digits
        self.assertFalse(is_valid)

    def test_calculate_check_digit(self):
        """Test check digit calculation"""
        # Example: 756.1234.5678.9X - calculate X
        check_digit = OASIValidator.calculate_check_digit("756123456789")
        self.assertEqual(check_digit, 7)  # Expected check digit

        # Another example
        check_digit = OASIValidator.calculate_check_digit("756000000002")
        self.assertEqual(check_digit, 6)

    def test_validate_check_digit_valid(self):
        """Test check digit validation for valid OASI"""
        is_valid, calculated = OASIValidator.validate_check_digit("756.1234.5678.97")
        self.assertTrue(is_valid)
        self.assertEqual(calculated, 7)

    def test_validate_check_digit_invalid(self):
        """Test check digit validation fails with wrong check digit"""
        is_valid, calculated = OASIValidator.validate_check_digit("756.1234.5678.96")
        self.assertFalse(is_valid)
        self.assertEqual(calculated, 7)  # Expected digit is 7, not 6

    def test_validate_check_digit_invalid_format(self):
        """Test check digit validation fails with invalid format"""
        with self.assertRaises(ValueError):
            OASIValidator.validate_check_digit("123.1234.5678.97")  # Wrong country

        with self.assertRaises(ValueError):
            OASIValidator.validate_check_digit("756.1234.567.97")  # Too short

    def test_is_valid_complete(self):
        """Test complete validation (format + check digit)"""
        self.assertTrue(OASIValidator.is_valid("756.1234.5678.97"))
        self.assertTrue(OASIValidator.is_valid("7561234567897"))

        self.assertFalse(OASIValidator.is_valid("756.1234.5678.96"))  # Wrong check digit
        self.assertFalse(OASIValidator.is_valid("123.1234.5678.97"))  # Wrong country
        self.assertFalse(OASIValidator.is_valid("756.1234.567.97"))   # Too short
        self.assertFalse(OASIValidator.is_valid(""))                   # Empty
        self.assertFalse(OASIValidator.is_valid(None))                 # None
        self.assertFalse(OASIValidator.is_valid("invalid"))            # Invalid

    def test_validate_or_raise_valid(self):
        """Test validate_or_raise doesn't raise for valid OASI"""
        try:
            OASIValidator.validate_or_raise("756.1234.5678.97")
            OASIValidator.validate_or_raise("7561234567897")
        except ValidationError:
            self.fail("validate_or_raise raised ValidationError for valid OASI")

    def test_validate_or_raise_empty(self):
        """Test validate_or_raise allows empty values"""
        try:
            OASIValidator.validate_or_raise("")
            OASIValidator.validate_or_raise(None)
        except ValidationError:
            self.fail("validate_or_raise shouldn't raise for empty values")

    def test_validate_or_raise_invalid_format(self):
        """Test validate_or_raise raises for invalid format"""
        with self.assertRaises(ValidationError):
            OASIValidator.validate_or_raise("123.1234.5678.97", field_name="OASI")

        with self.assertRaises(ValidationError):
            OASIValidator.validate_or_raise("756.1234.567.97", field_name="OASI")

    def test_validate_or_raise_invalid_check_digit(self):
        """Test validate_or_raise raises for invalid check digit"""
        with self.assertRaises(ValidationError):
            OASIValidator.validate_or_raise("756.1234.5678.96", field_name="OASI")


class OASIValidationExamples:
    """
    Code examples demonstrating OASI validation usage

    These are not actual tests but documentation/examples.
    """

    @staticmethod
    def example_1_standalone_validation():
        """Example 1: Standalone validation (no Odoo model)"""
        from ..models.oasi_validator import OASIValidator

        # Simple check
        if OASIValidator.is_valid("756.1234.5678.97"):
            print("✓ Valid OASI")
        else:
            print("✗ Invalid OASI")

        # Get formatted version
        sanitized = OASIValidator.sanitize("756 1234 5678 97")
        formatted = f"{sanitized[0:3]}.{sanitized[3:7]}.{sanitized[7:11]}.{sanitized[11:13]}"
        print(f"Formatted: {formatted}")

        # Calculate check digit
        check_digit = OASIValidator.calculate_check_digit("756123456789")
        print(f"Check digit for 756123456789: {check_digit}")

    @staticmethod
    def example_2_model_with_mixin():
        """Example 2: Using mixin in custom model"""
        # This would be in your models.py file:

        """
        from odoo import api, fields, models
        
        class InsurancePolicy(models.Model):
            _name = 'insurance.policy'
            _inherit = ['insurance.policy', 'oasi.validation.mixin']  # Add mixin
            
            insured_oasi = fields.Char(
                string='Insured OASI',
                placeholder='756.XXXX.XXXX.XX',
                help='Swiss Social Security ID'
            )
            
            @api.constrains('insured_oasi')
            def _validate_insured_oasi(self):
                # This automatically validates the OASI field
                self._validate_oasi_field('insured_oasi', field_label='Insured OASI')
            
            def get_formatted_oasi(self):
                # Get nicely formatted OASI
                return super().get_formatted_oasi('insured_oasi', format_with_dots=True)
        """
        pass

    @staticmethod
    def example_3_conditional_validation():
        """Example 3: Conditional validation (e.g., only for Swiss)"""
        # This would be in your models.py file:

        """
        from odoo import api, fields, models
        from odoo.exceptions import ValidationError
        
        class PersonRecord(models.Model):
            _name = 'person.record'
            _inherit = ['person.record', 'oasi.validation.mixin']
            
            country_id = fields.Many2one('res.country')
            identification_number = fields.Char()
            
            @api.constrains('identification_number', 'country_id')
            def _validate_identification(self):
                from ..models.oasi_validator import OASIValidator
                
                for record in self:
                    if record.country_id and record.country_id.code == 'CH':
                        if record.identification_number:
                            OASIValidator.validate_or_raise(
                                record.identification_number,
                                field_name='Identification Number'
                            )
        """
        pass

    @staticmethod
    def example_4_api_validation():
        """Example 4: Validation in API/controller"""
        # This would be in your controllers.py file:

        """
        from odoo import http
        from odoo.http import request
        from odoo.exceptions import ValidationError
        from ..models.oasi_validator import OASIValidator
        
        class OASIController(http.Controller):
            @http.route('/api/validate-oasi', type='json', auth='user')
            def validate_oasi(self, oasi_number):
                try:
                    OASIValidator.validate_or_raise(oasi_number, field_name='OASI')
                    return {'valid': True, 'message': 'OASI is valid'}
                except ValidationError as e:
                    return {'valid': False, 'error': str(e)}
        """
        pass

    @staticmethod
    def example_5_bulk_validation():
        """Example 5: Bulk validation of records"""
        # This would be usage code:

        """
        from ..models.oasi_validator import OASIValidator
        
        records = env['insurance.policy'].search([])
        
        # Find records with invalid OASI
        invalid_records = []
        for record in records:
            if record.insured_oasi and not OASIValidator.is_valid(record.insured_oasi):
                invalid_records.append(record.name)
        
        if invalid_records:
            print(f"Invalid OASI in: {', '.join(invalid_records)}")
        """
        pass


# Test Data - Valid and Invalid Examples

VALID_OASI_EXAMPLES = [
    ("756.1234.5678.97", "Format with dots"),
    ("7561234567897", "Format without dots"),
    ("756 1234 5678 97", "Format with spaces"),
]

INVALID_OASI_EXAMPLES = [
    ("123.1234.5678.97", "Wrong country code (not 756)"),
    ("756.1234.5678.96", "Wrong check digit"),
    ("756.1234.567.97", "Too short (12 digits instead of 13)"),
    ("756.1234.5678.970", "Too long (14 digits)"),
    ("abc.defg.hijk.lm", "Contains letters"),
    ("", "Empty string"),
    ("756000000000", "All zeros except country code"),
]

# Real-world test cases (with valid check digits)
# Note: These are synthetic examples, not real OASIs

REAL_WORLD_EXAMPLES = {
    "756.0000.0000.09": "Synthetic low number",
    "756.1234.5678.97": "Synthetic mid-range number",
    "756.9999.9999.90": "Synthetic high number",
}
