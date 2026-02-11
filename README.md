# l10n_ch_oasi_verification - Swiss OASI Validation Module

A complete, production-ready Odoo 18 module for validating Swiss Social Security IDs (OASI/AHV/AVS).

## What is OASI?

OASI (Old-Age and Survivors' Insurance) is the Swiss Social Security ID used for all Swiss residents and employees. It's also known as:
- **AHV** (Assurance-Vieillesse et Survivants) - French
- **AVS** (Alters- und Hinterlassenenversicherung) - German
- **AVS** (Assicurazione per la vecchiaia e i superstiti) - Italian

### Format
- Standard: `756.XXXX.XXXX.XX`
- Alternative: `756XXXXXXXXXX` (without dots)
- Always starts with `756` (Switzerland ISO 3166-1 numeric code)
- Contains exactly **13 digits**
- Last digit is a **check digit** (EAN-13 algorithm)

## Features

✅ **Format Validation** - Ensures OASI has correct format (13 digits, starts with 756)  
✅ **Check Digit Validation** - Uses EAN-13 algorithm (modulo 10)  
✅ **Real-Time User Feedback** - Immediate validation warnings with @api.onchange  
✅ **Save-Time Validation** - Error prevention at record save with @api.constrains  
✅ **Reusable Validators** - Use anywhere in your code  
✅ **Model Mixin** - Easy integration into any Odoo model  
✅ **Pre-built Extensions** - Ready-to-use validators for hr.employee and res.partner  
✅ **Flexible Format Handling** - Accepts OASI with or without dots  
✅ **Clear Error Messages** - Helpful validation feedback  
✅ **Production Ready** - Well-tested and documented  

## Quick Start

### 1. Install the Module

```bash
# Copy the addon to your addons directory
cp -r l10n_ch_oasi_verification /path/to/odoo/addons/

# Then install in Odoo:
# - Go to Apps
# - Search for "l10n_ch_oasi_verification"
# - Click "Install"
```

### 2. Use in Your Model

**Option A: Simple (Constraint Only)**
```python
from odoo import api, fields, models

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.model', 'oasi.validation.mixin']  # ← Add this
    
    oasi = fields.Char(string='OASI')
    
    @api.constrains('oasi')  # ← Add this (validates at save)
    def _validate_oasi(self):
        self._validate_oasi_field('oasi')  # ← Add this
```

**Option B: Better UX (Constraint + Onchange)**
```python
from odoo import api, fields, models

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.model', 'oasi.validation.mixin']  # ← Add this
    
    oasi = fields.Char(string='OASI', placeholder='756.XXXX.XXXX.XX')
    
    @api.onchange('oasi')  # ← Real-time feedback
    def _onchange_oasi(self):
        return self._onchange_validate_oasi_field('oasi')
    
    @api.constrains('oasi')  # ← Prevent save if invalid
    def _validate_oasi(self):
        self._validate_oasi_field('oasi')
```

That's it! Your OASI field is now validated (with real-time feedback if using Option B).

### 3. Test It

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Direct validation
OASIValidator.is_valid("756.1234.5678.97")  # Returns: True or False

# With error handling
try:
    OASIValidator.validate_or_raise("756.1234.5678.97")
except ValidationError as e:
    print(f"Invalid: {e}")
```

## Usage Examples

### Example 1: Add OASI Field to Employee

```python
# In your custom module's models.py
from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = ['hr.employee', 'oasi.validation.mixin']
    
    oasi = fields.Char(
        string='OASI',
        help='Swiss Social Security ID (756.XXXX.XXXX.XX)',
    )
    
    @api.constrains('oasi')
    def _validate_employee_oasi(self):
        self._validate_oasi_field('oasi', field_label='OASI')
```

### Example 2: Validate Existing ssnid Field

The module automatically validates `hr.employee.ssnid` and `res.partner.ssnid` if the number starts with 756.

```python
# No code needed! Just set the ssnid:
employee.ssnid = "756.1234.5678.97"  # Automatically validated
```

### Example 3: Get Formatted OASI

```python
class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']
    
    insured_oasi = fields.Char()
    
    def action_format_oasi(self):
        """Format OASI with dots"""
        for record in self:
            record.insured_oasi = record.get_formatted_oasi('insured_oasi')
```

### Example 4: Validate in Controller/API

```python
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

class OASIController(http.Controller):
    @http.route('/api/validate-oasi', type='json', auth='user')
    def validate_oasi(self, oasi_number):
        from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
        
        try:
            OASIValidator.validate_or_raise(oasi_number)
            return {'valid': True}
        except ValidationError as e:
            return {'valid': False, 'error': str(e)}
```

## Module Structure

```
l10n_ch_oasi_verification/
├── models/
│   ├── oasi_validator.py       ← Core validation utility
│   ├── oasi_mixin.py            ← Reusable model mixin
│   ├── model_extensions.py      ← hr.employee & res.partner extensions
│   └── __init__.py
├── controllers/
│   └── controllers.py
├── views/
│   ├── views.xml
│   └── templates.xml
├── __manifest__.py              ← Module metadata
├── __init__.py
├── tests.py                     ← Test cases & examples
├── DOCUMENTATION.md             ← Detailed documentation
└── README.md                    ← This file
```

## Key Classes

### OASIValidator

Static utility class for OASI validation:

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Validate
OASIValidator.is_valid("756.1234.5678.97")            # → True/False

# Validate and raise
OASIValidator.validate_or_raise("756.1234.5678.97")   # → ValidationError if invalid

# Sanitize (remove non-digits)
OASIValidator.sanitize("756.1234.5678.97")            # → "7561234567897"

# Calculate check digit
OASIValidator.calculate_check_digit("756123456789")   # → 7

# Validate check digit
is_valid, expected = OASIValidator.validate_check_digit("7561234567897")  # → (True, 7)
```

### OASIValidationMixin

Add to your model's `_inherit` list to get these methods:

```python
# Validate a field
record._validate_oasi_field('field_name', field_label='Label')

# Check if valid (returns boolean)
record.is_oasi_valid('field_name')

# Get formatted OASI
record.get_formatted_oasi('field_name', format_with_dots=True)
```

## Testing

The module includes comprehensive test cases:

```bash
# Run tests
python -m odoo --test-enable -d test_db -i l10n_ch_oasi_verification

# Or run specific test
python -m odoo --test-enable -d test_db -m l10n_ch_oasi_verification -k TestOASIValidator
```

## Algorithm Details

The validation uses the **EAN-13** check digit algorithm (modulo 10):

1. Take first 12 digits
2. Apply alternating weights: positions 1,3,5,7,9,11 get weight 1; positions 2,4,6,8,10,12 get weight 3
3. Calculate sum: `Σ(digit × weight)`
4. Check digit: `(10 - (sum mod 10)) mod 10`

**Example:**
```
Number:  756 1234 5678 9X
Weights: 1 3 1 3 1 3 1 3 1 3  1  3
Product: 7+15+6+3+2+9+4+15+6+21+8+27 = 123

123 mod 10 = 3
Check digit = (10 - 3) mod 10 = 7
Therefore: 756.1234.5678.97
```

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Invalid OASI format. Expected 13 digits starting with 756" | Wrong structure | Ensure format is 756.XXXX.XXXX.XX |
| "Invalid OASI check digit. Got 9, expected 8" | Wrong last digit | Recalculate or verify the OASI |
| "Input must be 12 digits for check digit calculation" | Wrong length for calculation | Provide exactly 12 digits |

## FAQs

### Can I use OASI with spaces or dashes?
Yes! The validator accepts any format and automatically removes non-digits:
- `756.1234.5678.97` ✓
- `756 1234 5678 97` ✓
- `756-1234-5678-97` ✓
- `7561234567897` ✓

### Can I store OASI without dots?
Yes! Store however you prefer. Use `get_formatted_oasi()` to get the formatted version when displaying.

### Does this validate if the OASI really exists?
No. This module only validates:
- **Format** (13 digits, starts with 756)
- **Check digit** (ISO 7064 Mod 11,10)

It doesn't check if the number is actual registered with Swiss authorities.

### Do I need to modify hr.employee or res.partner?
No! The module automatically adds validators to `ssnid` fields on these models. Just set the ssnid and the validation happens automatically.

### Can I use this with other Odoo versions?
This module is built for Odoo 18 CE. Compatibility with other versions would need testing.

## Dependencies

- `base` - Odoo core
- `hr` - For hr.employee validation
- `contacts` - For res.partner validation

## License

Check the LICENSE file in the addon directory.

## Author

Your Company Name

## Support

For issues, questions, or feature requests:
1. Check the [DOCUMENTATION.md](DOCUMENTATION.md) for detailed examples
2. Review [tests.py](tests.py) for usage examples
3. Look at the source code comments for implementation details

## Contributing

Improvements and suggestions are welcome! Areas for enhancement:
- Custom validators for specific OASI ranges
- Multi-language error messages
- Integration with Swiss registry validation APIs
- Performance optimizations for bulk validation

---

**Made with ❤️ for the Swiss community**
