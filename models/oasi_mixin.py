# -*- coding: utf-8 -*-
"""
OASI Validation Mixin

This mixin provides OASI validation functionality that can be added to any model.
It automatically validates OASI fields using the EAN-13 algorithm (modulo 10).

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

    def _get_environment_type(self):
        """Read and normalize environment type from ir.config.parameter."""
        if "environment_type" in self.env.context:
            return OASIValidator.normalize_environment_type(
                self.env.context.get("environment_type")
            )

        environment_type = self.env["ir.config.parameter"].sudo().get_param(
            "environment_type",
            default=OASIValidator.ENV_TYPE_PRODUCTION,
        )
        return OASIValidator.normalize_environment_type(environment_type)

    def _is_non_production_environment(self):
        """Return True for staging/development runtimes."""
        if "oasi_allow_test_range" in self.env.context:
            return bool(self.env.context.get("oasi_allow_test_range"))

        return OASIValidator.is_non_production_environment_type(
            self._get_environment_type()
        )

    def _ensure_oasi_is_unique(self, field_name, sanitized_oasi, field_label):
        """Ensure same sanitized OASI is not already assigned in the system."""
        duplicate_record, duplicate_model = self._find_oasi_duplicate_record(
            field_name=field_name,
            sanitized_oasi=sanitized_oasi,
            current_record=self,
        )

        if duplicate_record:
            raise ValidationError(
                f"OASI Mixin: "
                f"{field_label} {sanitized_oasi} is already assigned "
                f"(model: {duplicate_model}, record ID: {duplicate_record.id})."
            )

    def _get_oasi_source_identity(self, record, field_name):
        """Return canonical identity for the source record behind a field value."""
        field = record._fields.get(field_name)
        if not field:
            return None

        # For related fields, compare the underlying source record/field identity.
        related_path = getattr(field, "related", None)
        if related_path:
            # Normalize related_path to tuple (handle both string and tuple formats)
            if isinstance(related_path, str):
                related_path = tuple(related_path.split('.'))
            
            source_record = record
            for relation_name in related_path[:-1]:
                source_record = source_record[relation_name]
                if not source_record:
                    return None
            source_record = source_record[:1]
            if not source_record.id:
                return None
            return (source_record._name, source_record.id, related_path[-1])

        if not record.id:
            return None
        return (record._name, record.id, field_name)

    def _is_same_oasi_source(self, current_record, current_field_name, other_record, other_field_name):
        """Return True when two values point to the same logical source entity."""
        current_identity = self._get_oasi_source_identity(current_record, current_field_name)
        other_identity = self._get_oasi_source_identity(other_record, other_field_name)
        return bool(current_identity and other_identity and current_identity == other_identity)

    def _find_oasi_duplicate_record(self, field_name, sanitized_oasi, current_record=None):
        """
        Find first duplicate OASI record within the same model.
        
        Only searches within the current model to avoid false positives when
        different models use related fields pointing to the same source.
        """
        current = (current_record or self)[:1]
        model = self.env[self._name].sudo().with_context(active_test=False)
        
        domain = [(field_name, "!=", False)]
        if self.ids:
            domain.append(("id", "not in", self.ids))

        candidates = model.search(domain)
        for candidate in candidates:
            candidate_oasi = OASIValidator.sanitize(getattr(candidate, field_name, None))
            if candidate_oasi != sanitized_oasi:
                continue
            if current and self._is_same_oasi_source(
                current_record=current,
                current_field_name=field_name,
                other_record=candidate,
                other_field_name=field_name,
            ):
                continue
            return candidate, self._name

        return None, None

    def _validate_oasi_business_rules(self, field_name, field_label, oasi_value):
        """Apply environment and uniqueness rules after format/check-digit validation."""
        sanitized = OASIValidator.sanitize(oasi_value)
        is_test_range = OASIValidator.is_test_range(sanitized)

        if is_test_range and not self._is_non_production_environment():
            raise ValidationError(
                f"{field_label} in test range "
                "(756.9900.0000.00 - 756.9999.9999.99) "
                "is not allowed in production environments."
            )

        if not is_test_range:
            self._ensure_oasi_is_unique(field_name, sanitized, field_label)

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
                record._validate_oasi_business_rules(
                    field_name=field_name,
                    field_label=field_label,
                    oasi_value=oasi_value,
                )

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

        sanitized = OASIValidator.sanitize(oasi_value)
        if (
            OASIValidator.is_test_range(sanitized)
            and not self._is_non_production_environment()
        ):
            return {
                'warning': {
                    'title': f'Invalid {field_label}',
                    'message': (
                        f"{field_label} in test range "
                        "(756.9900.0000.00 - 756.9999.9999.99) "
                        "is not allowed in production environments."
                    ),
                }
            }

        if not OASIValidator.is_test_range(sanitized):
            duplicate_record, duplicate_model = self._find_oasi_duplicate_record(
                field_name=field_name,
                sanitized_oasi=sanitized,
                current_record=self,
            )
            if duplicate_record:
                return {
                    'warning': {
                        'title': f'Duplicate {field_label}',
                        'message': (
                            f"{field_label} {sanitized} is already assigned "
                            f"(model: {duplicate_model}, "
                            f"record ID: {duplicate_record.id})."
                        ),
                    }
                }
        
        return None  # Valid OASI
