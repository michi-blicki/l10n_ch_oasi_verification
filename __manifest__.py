# -*- coding: utf-8 -*-
{
    'name': "l10n_ch_oasi_verification",

    'summary': "Swiss OASI (Social Security ID) validation using ISO 7064 Mod 11,10",

    'description': """
        Swiss OASI/AHV/AVS Verification Module
        ========================================

        This module provides validation utilities for Swiss Social Security IDs (OASI).
        The OASI is a 13-digit number with format 756.XXXX.XXXX.XX (or without dots).

        Features:
        - Format validation (13 digits starting with 756 - Switzerland ISO 3166-1 numeric)
        - Check digit validation using ISO 7064 Mod 11,10 algorithm
        - Reusable validation utilities that can be integrated into any model
        - Pre-built validators for hr.employee and res.partner ssnid fields
        - Easy-to-use mixin for custom models

        Usage:
        ------
        Add to your model:
            _inherit = ['your.model', 'oasi.validation.mixin']
            
        Then use the validation in a constraint:
            @api.constrains('oasi_field')
            def _validate_oasi(self):
                self._validate_oasi_field('oasi_field')
    """,

    'author': "Michael Blickenstorfer, AI-assisted by Claude Haiku 4.5",
    'website': "https://github.com/michi-blicki/l10n_ch_oasi_verification/",
    'license': 'AGPL-3',
    
    'installable': True,
    'application': False,
    'auto_install': False,

    'category': 'Localization/Switzerland',
    'version': '18.0.1.0.0',

    'depends': ['base'],

    'data': [
    ],

    'demo': [
    ],
}

