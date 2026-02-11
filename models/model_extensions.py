# -*- coding: utf-8 -*-
"""
Model extensions for OASI validation

This module extends hr.employee and res.partner models to include OASI validation
on their ssnid fields.
"""

from odoo import api, fields, models


class HrEmployee(models.Model):
    """Extend hr.employee to validate OASI in ssnid field"""

    _inherit = "hr.employee"
    _inherit_oasi = True  # Flag to show this model includes OASI validation

    @api.constrains("ssnid")
    def _validate_employee_ssnid(self):
        """Validate OASI check digit if ssnid is set and looks like Swiss ID"""
        from .oasi_validator import OASIValidator

        for record in self:
            ssnid = record.ssnid
            if ssnid:
                # Only validate if it looks like a Swiss ID (starts with 756)
                sanitized = OASIValidator.sanitize(ssnid)
                if sanitized.startswith("756"):
                    try:
                        OASIValidator.validate_or_raise(ssnid, field_name="SSNID")
                    except Exception:
                        raise

    @api.onchange("ssnid")
    def _onchange_employee_ssnid(self):
        """Validate OASI on field change (real-time feedback to user)"""
        from .oasi_validator import OASIValidator

        ssnid = self.ssnid
        if ssnid:
            # Only validate if it looks like a Swiss ID (starts with 756)
            sanitized = OASIValidator.sanitize(ssnid)
            if sanitized.startswith("756"):
                return self._onchange_validate_oasi_field("ssnid", field_label="SSNID")
