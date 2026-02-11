# OASI Validation - Quick Reference

## Import

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
```

## 5-Second Usage

### Validate Single OASI
```python
if OASIValidator.is_valid("756.1234.5678.97"):
    print("Valid!")
```

### Add to Your Model (Constraint Only)
```python
class MyModel(models.Model):
    _inherit = ['my.model', 'oasi.validation.mixin']
    
    @api.constrains('oasi_field')
    def _validate_oasi(self):
        self._validate_oasi_field('oasi_field')
```

### Add to Your Model (With Real-Time Feedback)
```python
class MyModel(models.Model):
    _inherit = ['my.model', 'oasi.validation.mixin']
    
    # Real-time validation (user gets warning on field exit)
    @api.onchange('oasi_field')
    def _onchange_oasi(self):
        return self._onchange_validate_oasi_field('oasi_field')
    
    # Save-time validation (prevents invalid data)
    @api.constrains('oasi_field')
    def _validate_oasi(self):
        self._validate_oasi_field('oasi_field')
```

## Common Methods

| Method | Returns | Use Case |
|--------|---------|----------|
| `is_valid(oasi)` | `bool` | Simple true/false check |
| `validate_or_raise(oasi)` | None or raises | Use in constraints (raises ValidationError) |
| `sanitize(oasi)` | `str` | Remove dots/spaces/dashes |
| `calculate_check_digit(oasi12)` | `int` | Get check digit for 12 digits |
| `is_valid_format(oasi)` | `(bool, str)` | Check format only (not check digit) |
| `validate_check_digit(oasi)` | `(bool, int)` | Check digit validation with expected value |

## Mixin Methods

| Method | Returns | Use Case |
|--------|---------|----------|
| `_validate_oasi_field(field, label)` | None | Constraint validation (at save time) |
| `_onchange_validate_oasi_field(field, label)` | Dict or None | Onchange validation (real-time feedback) |
| `is_oasi_valid(field)` | `bool` | Check if field is valid |
| `get_formatted_oasi(field, dots)` | `str` | Get formatted version (with/without dots) |

## Formats (All Accepted)

✓ `756.1234.5678.97` - With dots  
✓ `7561234567897` - Without dots  
✓ `756 1234 5678 97` - With spaces  
✓ `756-1234-5678-97` - With dashes  
✓ Mixed formatting - All work!

## Valid Digits

- Total: **13 digits**
- Country code: **756** (always first 3)
- Check digit: **Last digit** (calculated)
- Replaceable with any digits: Positions 4-12

## Check Digit Algorithm

```
Input: 756123456789 (12 digits)
Weights: [5,4,3,2,7,6,5,4,3,2,7,6]
Sum = 7×5 + 5×4 + 6×3 + 1×2 + 2×7 + 3×6 + 4×5 + 5×4 + 6×3 + 7×2 + 8×7 + 9×6
    = 35 + 20 + 18 + 2 + 14 + 18 + 20 + 20 + 18 + 14 + 56 + 54 = 289
Check digit = (11 - (289 mod 11)) mod 10 = (11 - 3) mod 10 = 8
Result: 7561234567898
```

## Error Handling

```python
from odoo.exceptions import ValidationError

try:
    OASIValidator.validate_or_raise("invalid_oasi")
except ValidationError as e:
    print(f"Error: {e}")
    # Handle error
```

## Pre-configured Models

These models are already set up for OASI validation:

- `hr.employee` - Validates `ssnid` field if starts with 756
- `res.partner` - Validates `ssnid` field if starts with 756

## Model Examples

### Example 1: Simple Constraint
```python
class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']
    
    oasi = fields.Char('OASI')
    
    @api.constrains('oasi')
    def _validate_oasi(self):
        self._validate_oasi_field('oasi')
```

### Example 2: Multiple OASI Fields
```python
class GuardianshipCase(models.Model):
    _name = 'guardianship.case'
    _inherit = ['guardianship.case', 'oasi.validation.mixin']
    
    guardian_oasi = fields.Char('Guardian OASI')
    ward_oasi = fields.Char('Ward OASI')
    
    @api.constrains('guardian_oasi')
    def _validate_guardian(self):
        self._validate_oasi_field('guardian_oasi', field_label='Guardian OASI')
    
    @api.constrains('ward_oasi')
    def _validate_ward(self):
        self._validate_oasi_field('ward_oasi', field_label='Ward OASI')
```

### Example 3: Conditional Validation (Swiss Only)
```python
class PersonIdentification(models.Model):
    _name = 'person.identification'
    _inherit = ['person.identification', 'oasi.validation.mixin']
    
    country_id = fields.Many2one('res.country')
    id_number = fields.Char()
    
    @api.constrains('id_number', 'country_id')
    def _validate_id_number(self):
        for record in self:
            if record.country_id and record.country_id.code == 'CH':
                if record.id_number:
                    self._validate_oasi_field('id_number', field_label='ID Number')
```

### Example 4: Auto-format on Save
```python
class SwissEmployee(models.Model):
    _name = 'swiss.employee'
    _inherit = ['swiss.employee', 'oasi.validation.mixin']
    
    oasi = fields.Char('OASI')
    
    @api.model
    def create(self, values):
        if values.get('oasi'):
            values['oasi'] = self.get_formatted_oasi('oasi')
        record = super().create(values)
        return record
    
    def write(self, values):
        if values.get('oasi'):
            values['oasi'] = self.get_formatted_oasi('oasi')
        return super().write(values)
```

## Testing Standalone

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Test valid
assert OASIValidator.is_valid("756.1234.5678.97") == True
assert OASIValidator.is_valid("7561234567897") == True

# Test invalid
assert OASIValidator.is_valid("123.1234.5678.97") == False  # Wrong country
assert OASIValidator.is_valid("756.1234.5678.96") == False  # Wrong check digit
assert OASIValidator.is_valid("") == False                   # Empty

# Calculate check digit
assert OASIValidator.calculate_check_digit("756123456789") == 7
```

## Real-World OASI Examples

### Valid Examples
- `756.0000.0000.09`
- `756.1234.5678.97`
- `756.9999.9999.90`

### Common Errors
- `123.1234.5678.97` - Wrong country code (should be 756)
- `756.1234.5678.96` - Wrong check digit
- `756.123.5678.97` - Too short (12 digits, should be 13)
- `756.1234.5678.9701` - Too long (14 digits)

## Notes

- ✓ Accepts any formatting (dots, spaces, dashes, none)
- ✓ Allows empty/null values (validation only on set values)
- ✓ Clear error messages for debugging
- ✓ Validates format AND check digit
- ✗ Does NOT verify registration with Swiss authorities
- ✗ Does NOT validate non-Swiss numbers

## Cheat Sheet

```python
# Is it valid?
OASIValidator.is_valid(oasi_string)

# Raise error if not valid
OASIValidator.validate_or_raise(oasi_string)

# Get just the digits
OASIValidator.sanitize(oasi_string)

# Add to your model
_inherit = ['model', 'oasi.validation.mixin']

# Validate in constraint
@api.constrains('field')
def _validate(self):
    self._validate_oasi_field('field')
```

---

**For more details, see: README.md and DOCUMENTATION.md**
