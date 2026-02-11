# OASI Validation - @api.onchange Enhancement Summary

## What Was Added

Real-time OASI validation using `@api.onchange` decorator, providing immediate user feedback as they edit fields.

---

## New Features

### 1. **Real-Time Validation in Mixin**

#### New Method: `_onchange_validate_oasi_field(field_name, field_label=None)`

Located in: `models/oasi_mixin.py`

**Purpose:** Validate OASI when user edits the field, showing warnings immediately.

**Returns:**
- `None` if OASI is valid or empty
- Warning dictionary with error message if invalid

**Example:**
```python
from odoo import api, models

class MyModel(models.Model):
    _inherit = ['my.model', 'oasi.validation.mixin']
    
    oasi = fields.Char('OASI')
    
    @api.onchange('oasi')
    def _onchange_oasi(self):
        return self._onchange_validate_oasi_field('oasi', field_label='OASI')
```

### 2. **Updated Model Extensions**

Both `HrEmployee` and `ResPartner` now include:

#### Constraint Validation (Save-Time)
```python
@api.constrains("ssnid")
def _validate_employee_ssnid(self):
    """Prevents saving invalid OASI"""
```

#### Onchange Validation (Real-Time)
```python
@api.onchange("ssnid")
def _onchange_employee_ssnid(self):
    """Shows warning immediately when user edits"""
    return self._onchange_validate_oasi_field("ssnid", field_label="SSNID")
```

**Result:** Both `hr.employee` and `res.partner` now automatically validate OASI with:
- ⚠️ Warning when user enters invalid OASI
- 🚫 Error when trying to save invalid OASI

---

## Usage Patterns

### Pattern 1: Constraint Only (Minimal)
```python
@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

**Validation:** At save time only  
**User Feedback:** Error blocks save

### Pattern 2: Onchange + Constraint (Recommended)
```python
@api.onchange('oasi')
def _onchange_oasi(self):
    return self._onchange_validate_oasi_field('oasi')

@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

**Validation:** Real-time + save time  
**User Feedback:** Warning on edit + error on save attempt  
**UX:** Best experience for users

### Pattern 3: Multiple OASI Fields
```python
@api.onchange('guardian_oasi')
def _onchange_guardian_oasi(self):
    return self._onchange_validate_oasi_field('guardian_oasi', field_label='Guardian OASI')

@api.constrains('guardian_oasi')
def _validate_guardian_oasi(self):
    self._validate_oasi_field('guardian_oasi', field_label='Guardian OASI')

@api.onchange('ward_oasi')
def _onchange_ward_oasi(self):
    return self._onchange_validate_oasi_field('ward_oasi', field_label='Ward OASI')

@api.constrains('ward_oasi')
def _validate_ward_oasi(self):
    self._validate_oasi_field('ward_oasi', field_label='Ward OASI')
```

---

## Modified Files

### 1. `models/oasi_mixin.py`
- **Added:** `_onchange_validate_oasi_field()` method
- **Lines:** ~50 new lines
- **Purpose:** Provides onchange validation functionality

### 2. `models/model_extensions.py`
- **Added:** `_onchange_employee_ssnid()` method to `HrEmployee`
- **Added:** `_onchange_partner_ssnid()` method to `ResPartner`
- **Lines:** ~30 new lines
- **Purpose:** Real-time validation for employee and partner ssnid fields

### 3. `DEVELOPER_GUIDE.md`
- **Added:** Section 1.5 "Add Real-Time Validation with @api.onchange"
- **Added:** Use Case 4 "Employee with Real-Time Validation"
- **Updated:** Best Practices with onchange guidance
- **Purpose:** Documentation and examples

### 4. `QUICK_REFERENCE.md`
- **Updated:** Mixin Methods table to include `_onchange_validate_oasi_field`
- **Added:** Example showing both constraint and onchange usage
- **Purpose:** Quick reference for developers

### 5. `DOCUMENTATION.md`
- **Added:** Documentation for `_onchange_validate_oasi_field()` method
- **Updated:** Model Extensions section with onchange details
- **Purpose:** Complete technical documentation

### 6. `README.md`
- **Updated:** Features list to include "Real-Time User Feedback"
- **Updated:** "Use in Your Model" section with both approaches
- **Purpose:** User-facing documentation

---

## Error Message Format

When user enters invalid OASI and exits the field:

```
┌─────────────────────────────────────────────────────────┐
│  Invalid OASI                                           │
│  ─────────────────────────────────────────────────────  │
│  Invalid OASI format.                                   │
│  Expected 13 digits starting with 756, got: 123...     │
│                                                         │
│  [OK]                                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Benefits

✅ **Immediate Feedback** - Users see validation errors right away  
✅ **Better UX** - No surprises at save time  
✅ **Clear Errors** - Specific messages about what's wrong  
✅ **Dual Validation** - Real-time warning + save-time error prevention  
✅ **Backward Compatible** - Old constraint-only approach still works  
✅ **No Breaking Changes** - Existing code continues to work  

---

## Migration Guide (Optional)

If you want to add onchange validation to existing models:

**Before:**
```python
@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

**After:**
```python
@api.onchange('oasi')
def _onchange_oasi(self):
    return self._onchange_validate_oasi_field('oasi')

@api.constrains('oasi')
def _validate_oasi(self):
    self._validate_oasi_field('oasi')
```

Or even simpler using inheritance:
```python
# Inherit from model that already has onchange
class MyModel(models.Model):
    _inherit = ['existing.model', 'oasi.validation.mixin']
    
    # Pre-built models (hr.employee, res.partner) already have onchange!
```

---

## Testing the Enhancement

### In Odoo Form

1. Open employee or partner form
2. Enter invalid OASI in `ssnid` field: `756.invalid`
3. Click outside field → **Warning appears immediately**
4. Try to save → **Error blocks save**

### In Code

```python
# Test onchange validation
record = env['hr.employee'].new({'ssnid': '756.invalid'})
result = record._onchange_employee_ssnid()
print(result)
# Output: {'warning': {'title': 'Invalid SSNID', 'message': '...'}}

# Valid OASI
record = env['hr.employee'].new({'ssnid': '756.1234.5678.97'})
result = record._onchange_employee_ssnid()
print(result)
# Output: None (no warning)
```

---

## Technical Details

### How It Works

1. **User edits field** → `@api.onchange` triggered
2. **Method called** → `_onchange_validate_oasi_field()`
3. **Validation performed** → Format + check digit
4. **Result returned:**
   - Valid: `None` (no message)
   - Invalid: `{'warning': {'title': '...', 'message': '...'}}`
5. **User sees warning** → Yellow banner with error message
6. **User can correct** → Edit field and see new result

### When User Saves

1. **@api.constrains triggered**
2. **Full validation** → `_validate_oasi_field()`
3. **If invalid** → `ValidationError` prevents save
4. **If valid** → Record saved successfully

---

## Summary

The OASI validation module now supports:

✅ **Constraint-based validation** - At save time  
✅ **Onchange-based validation** - Real-time feedback  
✅ **Combined approach** - Best UX (recommended)  
✅ **Pre-built extensions** - Both approaches already included in hr.employee and res.partner  

Developers can choose their pattern based on UX requirements:
- **Simple:** Constraint-only (error at save)
- **Better:** Constraint + onchange (warning + error)
- **Best:** Inherit from extended models (automatic)

---

## Files Changed

```
l10n_ch_oasi_verification/
├── models/
│   ├── oasi_mixin.py              ✏️ Added _onchange_validate_oasi_field()
│   └── model_extensions.py         ✏️ Added onchange methods to HrEmployee & ResPartner
├── DEVELOPER_GUIDE.md              ✏️ Added onchange examples
├── QUICK_REFERENCE.md              ✏️ Updated mixin methods table
├── DOCUMENTATION.md                ✏️ Added _onchange_validate_oasi_field() docs
└── README.md                       ✏️ Updated features & usage examples
```

---

**All enhancements are backward compatible and production-ready! ✅**
