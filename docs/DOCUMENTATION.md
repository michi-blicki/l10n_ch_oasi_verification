# OASI Validation Module Documentation

## Overview

The `l10n_ch_oasi_verification` module provides a robust, reusable validation system for Swiss Social Security IDs (OASI/AHV/AVS).

### OASI Format
- **Standard Format**: 756.XXXX.XXXX.XX
- **Alternative Format**: 756XXXXXXXXXX (without dots)
- **Country Code**: 756 (Switzerland ISO 3166-1 numeric)
- **Total Digits**: 13
- **Check Digit**: Last digit calculated using ISO 7064 Mod 11,10

## Components

### 1. OASIValidator Class (`models/oasi_validator.py`)

The core validation utility that can be used standalone without Odoo models.

#### Key Methods

##### `sanitize(oasi_string)`
Remove all non-digit characters from OASI string.

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

oasi = "756.1234.5678.90"
sanitized = OASIValidator.sanitize(oasi)
# Result: "7561234567890"
```

##### `is_valid(oasi_string)`
Complete validation (format + check digit). Returns boolean.

```python
OASIValidator.is_valid("756.1234.5678.90")  # True/False
OASIValidator.is_valid("7561234567890")     # True/False
OASIValidator.is_valid("invalid")           # False
```

##### `validate_or_raise(oasi_string, field_name='OASI')`
Validate and raise `ValidationError` if invalid. Perfect for constraints.

```python
OASIValidator.validate_or_raise("756.1234.5678.90", field_name="Employee SSN")
# Raises ValidationError if invalid
```

##### `validate_check_digit(oasi_string)`
Validate only the check digit. Returns tuple (is_valid, calculated_digit).

```python
is_valid, calculated = OASIValidator.validate_check_digit("7561234567890")
# Returns: (True/False, expected_check_digit)
```

##### `calculate_check_digit(oasi_string)`
Calculate the check digit for a 12-digit OASI.

```python
check_digit = OASIValidator.calculate_check_digit("756123456789")  # Returns: 0
```

### 2. OASIValidationMixin (`models/oasi_mixin.py`)

Abstract model mixin that provides OASI validation methods for any Odoo model.

#### Methods

##### `_validate_oasi_field(field_name, field_label=None)`
Validate OASI in a specific field. Use in `@api.constrains`.

```python
from odoo import api, models

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.model', 'oasi.validation.mixin']
    
    oasi_number = fields.Char(string='OASI')
    
    @api.constrains('oasi_number')
    def _validate_oasi(self):
        self._validate_oasi_field('oasi_number', field_label='OASI Number')
```

##### `is_oasi_valid(field_name)`
Check if OASI in a field is valid. Returns boolean.

```python
if record.is_oasi_valid('oasi_number'):
    print("OASI is valid")
```

##### `_onchange_validate_oasi_field(field_name, field_label=None)`
Validate OASI on field change (real-time user feedback). Returns a warning dict if invalid, None if valid.

Use in `@api.onchange` decorator to provide immediate feedback as users edit the field.

```python
from odoo import api, models

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.model', 'oasi.validation.mixin']
    
    oasi_number = fields.Char(string='OASI')
    
    @api.onchange('oasi_number')
    def _onchange_oasi(self):
        # Shows warning immediately if user enters invalid OASI
        return self._onchange_validate_oasi_field('oasi_number', field_label='OASI Number')
    
    @api.constrains('oasi_number')
    def _validate_oasi(self):
        # Prevents saving invalid OASI
        self._validate_oasi_field('oasi_number', field_label='OASI Number')
```

The method returns:
- `None` if OASI is valid or empty
- A dict with warning message if OASI is invalid

```python
{
    'warning': {
        'title': 'Invalid OASI Number',
        'message': 'Invalid OASI Number format. Expected 13 digits starting with 756, got: 123...'
    }
}
```

##### `get_formatted_oasi(field_name, format_with_dots=True)`
Get formatted OASI from a field.

```python
# With dots (default)
formatted = record.get_formatted_oasi('oasi_number')  # Returns: "756.XXXX.XXXX.XX"

# Without dots
formatted = record.get_formatted_oasi('oasi_number', format_with_dots=False)  # Returns: "756XXXXXXXXXX"
```

### 3. Model Extensions (`models/model_extensions.py`)

Pre-built validators for common models with both constraint and onchange validation:

#### `HrEmployee` Extension
Automatically validates OASI in `hr.employee.ssnid` field (if Swiss).

**Includes:**
- `@api.constrains('ssnid')` - Prevents saving invalid OASI
- `@api.onchange('ssnid')` - Shows warning immediately when user edits

```python
# In hr.employee records, ssnid is now validated if it starts with "756"
# Real-time warning on edit, save-time error prevention

employee.ssnid = "756.1234.5678.90"  # Valid - saves without warnings
employee.ssnid = "756.invalid"  # Invalid - user sees warning on exit
# Attempting to save: Error blocks save
```

#### `ResPartner` Extension
Automatically validates OASI in `res.partner.ssnid` field (if Swiss).

**Includes:**
- `@api.constrains('ssnid')` - Prevents saving invalid OASI
- `@api.onchange('ssnid')` - Shows warning immediately when user edits

```python
# In res.partner records, ssnid is now validated if it starts with "756"
# Real-time warning on edit, save-time error prevention

partner.ssnid = "756.1234.5678.90"  # Valid - saves without warnings
partner.ssnid = "invalid"  # Not Swiss (no validation - only if starts with 756)
partner.ssnid = "756.invalid"  # Invalid Swiss - user sees warning on exit
```

**No code needed!** Both models are automatically extended with full OASI validation including real-time feedback.

## Usage Examples

### Example 1: Validate OASI Standalone (No Odoo Model)

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Simple validation
if OASIValidator.is_valid("756.1234.5678.90"):
    print("Valid OASI")
else:
    print("Invalid OASI")

# Validation with error handling
try:
    OASIValidator.validate_or_raise("756.1234.5678.90")
    print("OASI is valid")
except ValidationError as e:
    print(f"Invalid: {e}")
```

### Example 2: Add OASI Validation to Custom Model

```python
from odoo import api, fields, models

class EmployeeLeaveRequest(models.Model):
    _name = 'employee.leave.request'
    _inherit = ['employee.leave.request', 'oasi.validation.mixin']
    
    employee_oasi = fields.Char(string='Employee OASI')
    
    @api.constrains('employee_oasi')
    def _validate_leave_oasi(self):
        """Validate OASI for leave request"""
        self._validate_oasi_field('employee_oasi', field_label='Employee OASI')
```

### Example 3: Custom Model with Formatting

```python
from odoo import api, fields, models

class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']
    
    insured_oasi = fields.Char(string='Insured OASI')
    
    @api.constrains('insured_oasi')
    def _validate_insured_oasi(self):
        self._validate_oasi_field('insured_oasi', field_label='Insured OASI')
    
    @api.model
    def create(self, values):
        record = super().create(values)
        # Auto-format the OASI when creating
        if record.insured_oasi:
            record.insured_oasi = record.get_formatted_oasi('insured_oasi')
        return record
```

### Example 4: Validation with Multiple OASI Fields

```python
from odoo import api, fields, models

class GuardianshipRequest(models.Model):
    _name = 'guardianship.request'
    _inherit = ['guardianship.request', 'oasi.validation.mixin']
    
    guardian_oasi = fields.Char(string='Guardian OASI')
    ward_oasi = fields.Char(string='Ward OASI')
    
    @api.constrains('guardian_oasi')
    def _validate_guardian_oasi(self):
        self._validate_oasi_field('guardian_oasi', field_label='Guardian OASI')
    
    @api.constrains('ward_oasi')
    def _validate_ward_oasi(self):
        self._validate_oasi_field('ward_oasi', field_label='Ward OASI')
```

### Example 5: Conditional OASI Validation

```python
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class PersonRecord(models.Model):
    _name = 'person.record'
    _inherit = ['person.record', 'oasi.validation.mixin']
    
    country_id = fields.Many2one('res.country', string='Country')
    identification_number = fields.Char(string='ID Number')
    
    @api.constrains('identification_number', 'country_id')
    def _validate_identification(self):
        """Validate as OASI only if country is Switzerland"""
        from .oasi_validator import OASIValidator
        
        for record in self:
            if record.country_id and record.country_id.code == 'CH':
                # For Swiss residents, validate as OASI
                if record.identification_number:
                    OASIValidator.validate_or_raise(
                        record.identification_number,
                        field_name='Identification Number'
                    )
```

## Algorithm Details

### ISO 7064 Mod 11,10 Algorithm

The check digit is calculated as follows:

1. Take the first 12 digits of the OASI
2. Define weights: [5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 7, 6]
3. Calculate: `sum = Σ(digit[i] × weight[i])` for i = 0 to 11
4. Calculate: `check_digit = (11 - (sum mod 11)) mod 10`
5. The 13th digit is the check digit

### Example Calculation

For OASI `756123456789_` (where _ is check digit):

```
Digits:  7  5  6  1  2  3  4  5  6  7  8  9
Weights: 5  4  3  2  7  6  5  4  3  2  7  6
---------
Products: 35 20 18  2 14 18 20 20 18 14 56 54 = 289

289 mod 11 = 3
11 - 3 = 8
8 mod 10 = 8

Check digit = 8
```

## Error Messages

The module provides clear error messages:

```
"Invalid OASI format. Expected 13 digits starting with 756, got: 1234567890123"
"Invalid OASI check digit. Got 9, expected 8 (last digit)."
"Invalid OASI: Input must be 12 digits for check digit calculation"
```

## Testing

Example test cases:

```python
Valid OASI Examples:
- "756.1234.5678.97" → Valid with check digit 7
- "756123456789X" → Valid (replace X with correct check digit)

Invalid OASI Examples:
- "123.1234.5678.97" → Doesn't start with 756
- "756.1234.5678.96" → Wrong check digit
- "756.1234.567.97" → Only 12 digits
- "abc.defg.hijk.lm" → Contains non-numeric characters
```

## Integration with Forms

When integrating into Odoo forms, the validation happens automatically:

```xml
<!-- views/myview.xml -->
<form string="My Form">
    <field name="insured_oasi" widget="char" placeholder="756.XXXX.XXXX.XX"/>
    <!-- Validation is automatic on save -->
</form>
```

## Best Practices

1. **Use `validate_or_raise()` in constraints** - This ensures validation happens at save time
2. **Make OASI field optional** - Use constraints only when field is set
3. **Display formatted OASI** - Use `get_formatted_oasi()` for display
4. **Sanitize on input** - Use `OASIValidator.sanitize()` in create/write methods if storing without dots

## Dependencies

- `base` - Odoo core module
- `hr` - For `hr.employee` model (if using employee extension)
- `contacts` - For `res.partner` model (if using partner extension)

## Notes

- The validator accepts both formats: with and without dots (e.g., "756.1234.5678.97" or "756123456789X")
- Empty/null OASI values are allowed (validation only runs when value is set)
- The module only validates format and check digit - it doesn't verify if the OASI actually exists
- Swiss country check: Only validates as OASI if the number starts with 756
