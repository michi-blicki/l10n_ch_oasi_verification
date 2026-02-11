# OASI Validation Module - Developer Guide

## Overview

The `l10n_ch_oasi_verification` addon provides a complete, reusable solution for validating Swiss Social Security IDs (OASI) in Odoo 18. This guide shows developers how to integrate OASI validation into their custom modules.

---

## Architecture

### Three-Layer Approach

```
┌─────────────────────────────────────────────────┐
│         Your Model (Model Extensions)            │
│  - hr.employee, res.partner, custom models      │
│  - Use @api.constrains decorator                │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│      OASIValidationMixin (Odoo Models)          │
│  - _validate_oasi_field()                       │
│  - get_formatted_oasi()                         │
│  - is_oasi_valid()                              │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│       OASIValidator (Pure Python Utility)       │
│  - is_valid()                                   │
│  - validate_or_raise()                          │
│  - calculate_check_digit()                      │
│  - EAN-13 Algorithm (Modulo 10)                │
└─────────────────────────────────────────────────┘
```

### Module Structure

```
l10n_ch_oasi_verification/
├── models/
│   ├── __init__.py                   # Imports all modules
│   ├── oasi_validator.py             # Core validation logic (pure Python)
│   ├── oasi_mixin.py                 # Reusable mixin for Odoo models
│   ├── model_extensions.py           # Extensions to hr.employee & res.partner
│   └── models.py                     # Documentation file
├── controllers/                       # (Optional API endpoints)
├── views/                            # (Optional UI components)
├── tests.py                          # Test cases and examples
├── __manifest__.py                   # Module configuration
├── README.md                         # Quick start guide
├── QUICK_REFERENCE.md                # Cheat sheet
└── DOCUMENTATION.md                  # Detailed documentation
```

---

## How to Use in Your Module

### Scenario 1: Add OASI Validation to an Existing Model

Say you have a custom `insurance.policy` model and want to add OASI validation:

**Step 1:** Add the mixin to your model:

```python
# In your_module/models/insurance_policy.py

from odoo import api, fields, models

class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _description = 'Insurance Policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']  # ← Add mixin
    
    # Add your OASI field
    insured_oasi = fields.Char(
        string='Insured OASI',
        help='Swiss Social Security ID (756.XXXX.XXXX.XX)',
    )
    
    # Add constraint to validate
    @api.constrains('insured_oasi')
    def _validate_insured_oasi(self):
        self._validate_oasi_field('insured_oasi', field_label='Insured OASI')
```

**Step 2:** Update module dependencies:

```python
# In your_module/__manifest__.py

{
    'name': 'Insurance Module',
    'depends': [
        'base',
        'l10n_ch_oasi_verification',  # ← Add dependency
    ],
    # ... rest of manifest
}
```

**Step 3:** Test it:

```python
# Create a record with valid OASI
policy = env['insurance.policy'].create({
    'insured_oasi': '756.1234.5678.97'  # ✓ Valid - saves successfully
})

# Try invalid OASI
policy = env['insurance.policy'].create({
    'insured_oasi': '756.invalid.oasi.99'  # ✗ Error raised
})
```

---

### Scenario 2: Validate Existing ssnid Field

If you're using the standard `ssnid` field on `hr.employee` or `res.partner`:

```python
# No code needed! The module automatically validates ssnid if it starts with 756

# Just set the ssnid field
employee.ssnid = "756.1234.5678.97"  # Automatically validated ✓

# Or in controller
data = request.jsonrequest
employee = request.env['hr.employee'].create({
    'name': 'John Doe',
    'ssnid': data['oasi']  # Validation happens automatically
})
```

---

### Scenario 3: Conditional OASI Validation

Validate OASI only for Swiss employees:

```python
# In your_module/models/custom_employee.py

from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = ['hr.employee', 'oasi.validation.mixin']
    
    # Existing ssnid field is inherited from hr.employee
    
    @api.constrains('ssnid', 'address_id')
    def _validate_ssnid_by_country(self):
        """Validate OASI only for Swiss employees"""
        from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
        
        for record in self:
            if record.ssnid:
                # Check if employee is in Switzerland
                is_swiss = (record.address_id and 
                           record.address_id.country_id and 
                           record.address_id.country_id.code == 'CH')
                
                if is_swiss:
                    # Validate as OASI
                    self._validate_oasi_field('ssnid', field_label='SSNID')
```

---

### Scenario 4: Multiple OASI Fields

Validate multiple OASI fields in one model:

```python
from odoo import api, fields, models

class GuardianshipCase(models.Model):
    _name = 'guardianship.case'
    _inherit = ['guardianship.case', 'oasi.validation.mixin']
    
    guardian_oasi = fields.Char(string='Guardian OASI')
    ward_oasi = fields.Char(string='Ward OASI')
    
    @api.constrains('guardian_oasi')
    def _validate_guardian_oasi(self):
        self._validate_oasi_field('guardian_oasi', field_label='Guardian OASI')
    
    @api.constrains('ward_oasi')
    def _validate_ward_oasi(self):
        self._validate_oasi_field('ward_oasi', field_label='Ward OASI')
```

---

## Using OASIValidator Directly

### In Controllers/APIs

```python
# In your_module/controllers/api.py

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

class OASIAPIController(http.Controller):
    
    @http.route('/api/validate-oasi', type='json', auth='user')
    def validate_oasi(self, oasi_number):
        """REST API endpoint to validate OASI"""
        try:
            OASIValidator.validate_or_raise(oasi_number)
            return {
                'valid': True,
                'message': 'OASI is valid',
                'formatted': OASIValidator.sanitize(oasi_number)
            }
        except ValidationError as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @http.route('/api/format-oasi', type='json', auth='user')
    def format_oasi(self, oasi_number):
        """Format OASI with dots"""
        sanitized = OASIValidator.sanitize(oasi_number)
        formatted = f"{sanitized[0:3]}.{sanitized[3:7]}.{sanitized[7:11]}.{sanitized[11:13]}"
        return {'formatted': formatted}
    
    @http.route('/api/calculate-check-digit', type='json', auth='user')
    def get_check_digit(self, oasi_12_digits):
        """Calculate check digit for 12-digit basis"""
        try:
            check_digit = OASIValidator.calculate_check_digit(oasi_12_digits)
            return {'check_digit': check_digit}
        except ValueError as e:
            return {'error': str(e)}
```

### In Business Logic

```python
# In your_module/models/custom_logic.py

from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

def import_employees_from_file(file_content):
    """Import employees and validate OASIs"""
    employees = []
    errors = []
    
    for row in file_content:
        try:
            # Validate OASI before creating
            OASIValidator.validate_or_raise(
                row['oasi'],
                field_name=f"Employee {row['name']} OASI"
            )
            
            employees.append(row)
        except ValidationError as e:
            errors.append({
                'row': row,
                'error': str(e)
            })
    
    return employees, errors


def batch_validate_oasis(records):
    """Check which records have valid OASI"""
    from odoo.addons.l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
    
    results = {
        'valid': [],
        'invalid': []
    }
    
    for record in records:
        if OASIValidator.is_valid(record.oasi):
            results['valid'].append(record.id)
        else:
            results['invalid'].append({
                'id': record.id,
                'name': record.name,
                'oasi': record.oasi
            })
    
    return results
```

---

## Best Practices

### 1. Always Use Constraints

```python
# ✓ GOOD: Validation at save time
@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

```python
# ✗ AVOID: Validation only in create
@api.model
def create(self, values):
    # This doesn't catch updates!
    return super().create(values)
```

### 1.5. Add Real-Time Validation with @api.onchange

For better user experience, pair constraints with `@api.onchange` to give immediate feedback:

```python
# ✓ GOOD: Real-time validation + save-time validation
class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']
    
    insured_oasi = fields.Char(string='Insured OASI')
    
    # Real-time feedback as user types
    @api.onchange('insured_oasi')
    def _onchange_insured_oasi(self):
        return self._onchange_validate_oasi_field('insured_oasi', field_label='Insured OASI')
    
    # Final validation at save time
    @api.constrains('insured_oasi')
    def _validate_insured_oasi(self):
        self._validate_oasi_field('insured_oasi', field_label='Insured OASI')
```

The `_onchange_validate_oasi_field()` returns a warning dict that displays to the user immediately, while `_validate_oasi_field()` raises an error to prevent saving invalid data.

**Pre-built in extensions:**
Both `hr.employee` and `res.partner` models now include both `@api.constrains` and `@api.onchange` handlers automatically. No additional code needed!

```python
# Already included in hr.employee and res.partner
employee.ssnid = "756.invalid"  # Warning shows immediately on field exit
# Attempting to save: Error blocks save (constraint validation)
```

### 2. Make OASI Optional When Appropriate


```python
# ✓ GOOD: Allow empty values
@api.constrains('oasi')
def _validate_oasi(self):
    # validate_or_raise allows empty values
    self._validate_oasi_field('oasi')
```

```python
# ✗ AVOID: Requiring OASI if not needed
oasi = fields.Char(required=True)  # Too strict if optional
```

### 3. Provide Clear Field Labels

```python
# ✓ GOOD: Clear error messages
self._validate_oasi_field('employee_oasi', field_label='Employee OASI')
# Error: "Invalid Employee OASI format..."
```

```python
# ✗ AVOID: Generic labels
self._validate_oasi_field('ssnid')  # Error: "Invalid SSNID format..."
# Unclear what format is expected
```

### 4. Store Formatted When Possible

```python
# ✓ GOOD: Store with dots for readability
@api.model
def create(self, values):
    if values.get('oasi'):
        values['oasi'] = self.get_formatted_oasi('oasi')
    return super().create(values)
```

### 5. Document OASI Fields

```python
# ✓ GOOD: Clear help text
oasi = fields.Char(
    string='OASI',
    help='Swiss Social Security ID (format: 756.XXXX.XXXX.XX)',
)

# Add placeholder in web form
oasi = fields.Char(
    string='OASI',
    placeholder='756.XXXX.XXXX.XX',
)
```

---

## Testing Your Implementation

### Unit Testing

```python
# In your_module/tests/test_oasi_integration.py

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestInsurancePolicyOASI(TransactionCase):
    
    def test_valid_oasi(self):
        """Test that valid OASI is accepted"""
        policy = self.env['insurance.policy'].create({
            'insured_oasi': '756.1234.5678.97'
        })
        self.assertEqual(policy.insured_oasi, '756.1234.5678.97')
    
    def test_invalid_oasi_check_digit(self):
        """Test that invalid check digit is rejected"""
        with self.assertRaises(ValidationError):
            self.env['insurance.policy'].create({
                'insured_oasi': '756.1234.5678.96'  # Wrong check digit
            })
    
    def test_invalid_oasi_format(self):
        """Test that invalid format is rejected"""
        with self.assertRaises(ValidationError):
            self.env['insurance.policy'].create({
                'insured_oasi': '123.1234.5678.97'  # Wrong country code
            })
    
    def test_empty_oasi_allowed(self):
        """Test that empty OASI is allowed"""
        policy = self.env['insurance.policy'].create({
            'insured_oasi': ''  # Empty is OK
        })
        self.assertEqual(policy.insured_oasi, '')
```

### Manual Testing

```python
# In Odoo console or shell

# Test 1: Create with valid OASI
policy = env['insurance.policy'].create({
    'insured_oasi': '756.1234.5678.97'
})
print("✓ Valid OASI accepted")

# Test 2: Try invalid OASI
try:
    policy = env['insurance.policy'].create({
        'insured_oasi': '756.invalid.format.99'
    })
except Exception as e:
    print(f"✓ Invalid OASI rejected: {e}")

# Test 3: Update with invalid OASI
try:
    policy.write({'insured_oasi': '123.1234.5678.97'})
except Exception as e:
    print(f"✓ Invalid update rejected: {e}")

# Test 4: Formatting
policy = env['insurance.policy'].create({
    'insured_oasi': '7561234567897'
})
formatted = policy.get_formatted_oasi('insured_oasi')
print(f"Formatted: {formatted}")  # Should print: 756.1234.5678.97
```

---

## Troubleshooting

### Problem: Validation Not Running

**Cause:** Missing constraint decorator

```python
# ✗ WRONG
def _validate_oasi(self):
    self._validate_oasi_field('oasi')

# ✓ CORRECT
@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

### Problem: Module Not Found

**Cause:** Missing dependency in manifest

```python
# ✓ Fix: Add to manifest
{
    'depends': [
        'base',
        'l10n_ch_oasi_verification',  # ← Required
    ],
}
```

### Problem: Wrong Error Message

**Cause:** Not providing field label

```python
# ✗ Generic
self._validate_oasi_field('oasi')
# Error: "Invalid OASI format..."

# ✓ Clear
self._validate_oasi_field('oasi', field_label='Employee OASI')
# Error: "Invalid Employee OASI format..."
```

### Problem: Validation Too Strict

**Cause:** Making OASI required when not needed

```python
# ✗ Too strict
oasi = fields.Char(required=True)

# ✓ Better
oasi = fields.Char()  # Optional, validate only when set
# Validation runs in constraint only when field is not empty
```

---

## API Reference

### OASIValidator Methods

```python
from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Basic validation
OASIValidator.is_valid(oasi_string)  # → bool

# Validate and raise
OASIValidator.validate_or_raise(oasi_string, field_name='OASI')  # → ValidationError

# Utility methods
OASIValidator.sanitize(oasi_string)  # → str (digits only)
OASIValidator.is_valid_format(oasi_string)  # → (bool, str)
OASIValidator.validate_check_digit(oasi_string)  # → (bool, int)
OASIValidator.calculate_check_digit(oasi_12_digits)  # → int
```

### OASIValidationMixin Methods

```python
# In your model inheriting the mixin:

record._validate_oasi_field(field_name, field_label='Field')  # Constraint validation
record.is_oasi_valid(field_name)  # → bool
record.get_formatted_oasi(field_name, format_with_dots=True)  # → str
```

---

## Common Use Cases

### Use Case 1: Employee Onboarding Form

```python
class EmployeeOnboarding(models.Model):
    _name = 'employee.onboarding'
    _inherit = ['employee.onboarding', 'oasi.validation.mixin']
    
    employee_name = fields.Char('Employee Name')
    employee_oasi = fields.Char('OASI')
    
    @api.constrains('employee_oasi')
    def _validate_employee_oasi(self):
        self._validate_oasi_field('employee_oasi', field_label='Employee OASI')
```

### Use Case 2: Insurance Policy Management

```python
class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _inherit = ['insurance.policy', 'oasi.validation.mixin']
    
    insured_oasi = fields.Char('Insured OASI')
    
    @api.constrains('insured_oasi')
    def _validate_insured_oasi(self):
        self._validate_oasi_field('insured_oasi')
```

### Use Case 3: Guardianship/Custody Cases

```python
class GuardianshipCase(models.Model):
    _name = 'guardianship.case'
    _inherit = ['guardianship.case', 'oasi.validation.mixin']
    
    guardian_oasi = fields.Char('Guardian OASI')
    ward_oasi = fields.Char('Ward OASI')
    
    @api.constrains('guardian_oasi')
    def _validate_guardian_oasi(self):
        self._validate_oasi_field('guardian_oasi', field_label='Guardian OASI')
    
    @api.constrains('ward_oasi')
    def _validate_ward_oasi(self):
        self._validate_oasi_field('ward_oasi', field_label='Ward OASI')
```

### Use Case 4: Employee with Real-Time Validation

For best UX, combine `@api.onchange` (real-time feedback) with `@api.constrains` (prevent save):

```python
class HrEmployee(models.Model):
    _inherit = ['hr.employee', 'oasi.validation.mixin']
    
    oasi = fields.Char(
        'OASI',
        placeholder='756.XXXX.XXXX.XX',
        help='Swiss Social Security ID'
    )
    
    # Real-time validation - Shows warning immediately as user exits field
    @api.onchange('oasi')
    def _onchange_oasi(self):
        return self._onchange_validate_oasi_field('oasi', field_label='OASI')
    
    # Save-time validation - Prevents invalid data from being saved
    @api.constrains('oasi')
    def _validate_oasi(self):
        self._validate_oasi_field('oasi', field_label='OASI')
```

User experience:
- **Field change:** Warning appears immediately if OASI is invalid
- **Save attempt:** Error prevents save if OASI is invalid
- **Valid OASI:** Saves without warnings or errors


### Use Case 4: Benefit Claims

```python
class BenefitClaim(models.Model):
    _name = 'benefit.claim'
    _inherit = ['benefit.claim', 'oasi.validation.mixin']
    
    claimant_oasi = fields.Char('Claimant OASI')
    dependent_oasi = fields.Char('Dependent OASI')
    
    @api.constrains('claimant_oasi', 'dependent_oasi')
    def _validate_claim_oasis(self):
        self._validate_oasi_field('claimant_oasi', field_label='Claimant OASI')
        self._validate_oasi_field('dependent_oasi', field_label='Dependent OASI')
```

---

## Performance Considerations

- **Validation is lightweight:** Simple format check + modulo arithmetic
- **No external calls:** Pure Python implementation, no API calls
- **Suitable for bulk operations:** Can validate thousands of records quickly
- **No database overhead:** Validation doesn't require additional DB queries

---

## Support & Further Reading

- See [README.md](README.md) for quick start
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for cheat sheet
- See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed specs
- See [tests.py](tests.py) for more code examples

---

**Happy coding! 🇨🇭**
