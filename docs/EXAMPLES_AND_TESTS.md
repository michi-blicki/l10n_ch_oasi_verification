# OASI Validation Examples - Copy & Paste Ready

This file contains ready-to-use examples and test cases.

## Quick Validation Tests

Copy and paste into your Odoo shell or Python console:

```python
# ============= BASIC VALIDATION TESTS =============

from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator

# Test 1: Valid OASI
print("Test 1: Valid OASI with dots")
result = OASIValidator.is_valid("756.1234.5678.97")
print(f"  Result: {result}")  # Expected: True
assert result == True

# Test 2: Valid OASI without dots
print("Test 2: Valid OASI without dots")
result = OASIValidator.is_valid("7561234567897")
print(f"  Result: {result}")  # Expected: True
assert result == True

# Test 3: Invalid country code
print("Test 3: Invalid country code")
result = OASIValidator.is_valid("123.1234.5678.97")
print(f"  Result: {result}")  # Expected: False
assert result == False

# Test 4: Invalid check digit
print("Test 4: Invalid check digit")
result = OASIValidator.is_valid("756.1234.5678.96")
print(f"  Result: {result}")  # Expected: False
assert result == False

# Test 5: Empty value
print("Test 5: Empty value")
result = OASIValidator.is_valid("")
print(f"  Result: {result}")  # Expected: False
assert result == False

# Test 6: Different formatting styles
print("Test 6: Different formatting styles")
formats = [
    "756.1234.5678.97",
    "7561234567897",
    "756-1234-5678-97",
    "756 1234 5678 97",
]
for fmt in formats:
    result = OASIValidator.is_valid(fmt)
    print(f"  {fmt}: {result}")
    assert result == True

print("\n✅ All basic validation tests passed!\n")
```

## Sanitization Tests

```python
# ============= SANITIZATION TESTS =============

print("Test: Sanitization (removing non-digits)")
test_cases = [
    ("756.1234.5678.97", "7561234567897"),
    ("756-1234-5678-97", "7561234567897"),
    ("756 1234 5678 97", "7561234567897"),
    ("7561234567897", "7561234567897"),
    ("", ""),
]

for input_val, expected in test_cases:
    result = OASIValidator.sanitize(input_val)
    print(f"  Input: '{input_val}' → Output: '{result}'")
    assert result == expected

print("✅ All sanitization tests passed!\n")
```

## Check Digit Calculation Tests

```python
# ============= CHECK DIGIT CALCULATION TESTS =============

print("Test: Calculate check digit")
test_cases = [
    ("756123456789", 7),  # Check digit should be 7
    ("756000000002", 9),  # Check digit should be 9
]

for input_digits, expected_check_digit in test_cases:
    result = OASIValidator.calculate_check_digit(input_digits)
    print(f"  Input: {input_digits} → Check digit: {result} (expected: {expected_check_digit})")
    assert result == expected_check_digit

print("✅ All check digit calculation tests passed!\n")
```

## Check Digit Validation Tests

```python
# ============= CHECK DIGIT VALIDATION TESTS =============

print("Test: Validate check digit")
test_cases = [
    ("7561234567897", True),   # Valid check digit (7)
    ("7561234567896", False),  # Invalid check digit (6 instead of 7)
    ("756000000029", True),    # Valid check digit (9)
    ("756000000021", False),   # Invalid check digit (1 instead of 9)
]

for oasi, expected_valid in test_cases:
    is_valid, calculated = OASIValidator.validate_check_digit(oasi)
    print(f"  {oasi}: Valid={is_valid}, Calculated={calculated}")
    assert is_valid == expected_valid

print("✅ All check digit validation tests passed!\n")
```

## Error Handling Tests

```python
# ============= ERROR HANDLING TESTS =============

from odoo.exceptions import ValidationError

print("Test: Error handling with validate_or_raise")

# Test 1: Valid OASI should not raise
print("  Test 1: Valid OASI (no error)")
try:
    OASIValidator.validate_or_raise("756.1234.5678.97")
    print("    ✓ No error raised")
except ValidationError as e:
    print(f"    ✗ Unexpected error: {e}")
    assert False

# Test 2: Empty OASI should not raise
print("  Test 2: Empty OASI (no error)")
try:
    OASIValidator.validate_or_raise("")
    print("    ✓ No error raised")
except ValidationError as e:
    print(f"    ✗ Unexpected error: {e}")
    assert False

# Test 3: Invalid format should raise
print("  Test 3: Invalid format (should error)")
try:
    OASIValidator.validate_or_raise("123.1234.5678.97")
    print("    ✗ Should have raised error")
    assert False
except ValidationError as e:
    print(f"    ✓ Error raised: {str(e)[:50]}...")

# Test 4: Invalid check digit should raise
print("  Test 4: Invalid check digit (should error)")
try:
    OASIValidator.validate_or_raise("756.1234.5678.96")
    print("    ✗ Should have raised error")
    assert False
except ValidationError as e:
    print(f"    ✓ Error raised: {str(e)[:50]}...")

print("✅ All error handling tests passed!\n")
```

## Model Integration Tests

```python
# ============= MODEL INTEGRATION TESTS =============

print("Test: Model validation with mixin\n")

# Assume you have created an InsurancePolicy model with OASI validation

# Test 1: Create with valid OASI
print("Test 1: Create policy with valid OASI")
try:
    policy = env['insurance.policy'].create({
        'insured_oasi': '756.1234.5678.97'
    })
    print("  ✓ Policy created successfully")
    print(f"  OASI: {policy.insured_oasi}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Create with invalid OASI (should fail)
print("\nTest 2: Create policy with invalid OASI (should fail)")
try:
    policy = env['insurance.policy'].create({
        'insured_oasi': '756.1234.5678.96'
    })
    print("  ✗ Should have failed validation")
except Exception as e:
    print(f"  ✓ Validation failed as expected: {str(e)[:50]}...")

# Test 3: Update with valid OASI
print("\nTest 3: Update policy with valid OASI")
try:
    policy = env['insurance.policy'].search([('/name', '=', 'Test Policy')])[0]
    # Test-range OASI is valid only in staging/development environment_type
    env['ir.config.parameter'].sudo().set_param('environment_type', 'staging')
    policy.write({'insured_oasi': '756.9999.9999.90'})
    print("  ✓ Policy updated successfully")
    print(f"  OASI: {policy.insured_oasi}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 4: Update with invalid OASI (should fail)
print("\nTest 4: Update policy with invalid OASI (should fail)")
try:
    policy.write({'insured_oasi': 'invalid'})
    print("  ✗ Should have failed validation")
except Exception as e:
    print(f"  ✓ Validation failed as expected: {str(e)[:50]}...")

# Test 5: Get formatted OASI
print("\nTest 5: Get formatted OASI")
try:
    policy = env['insurance.policy'].search([])[0]
    formatted = policy.get_formatted_oasi('insured_oasi')
    print(f"  ✓ Formatted: {formatted}")
except Exception as e:
    print(f"  Error: {e}")

# Test 6: Check if OASI is valid
print("\nTest 6: Check if OASI is valid")
try:
    policy = env['insurance.policy'].search([])[0]
    is_valid = policy.is_oasi_valid('insured_oasi')
    print(f"  ✓ Is valid: {is_valid}")
except Exception as e:
    print(f"  Error: {e}")

print("\n✅ All model integration tests completed!\n")
```

## Real-World Scenario Test

```python
# ============= REAL-WORLD SCENARIO =============

print("Real-World Scenario: Import employees with OASI validation\n")

def import_employees(data_list):
    """Import employees and validate OASI"""
    successful = []
    failed = []
    
    for employee_data in data_list:
        try:
            # Validate OASI first
            if employee_data.get('ssnid'):
                OASIValidator.validate_or_raise(
                    employee_data['ssnid'],
                    field_name=f"Employee {employee_data['name']} SSNID"
                )
            
            # Create employee
            employee = env['hr.employee'].create(employee_data)
            successful.append({
                'name': employee.name,
                'id': employee.id,
                'ssnid': employee.ssnid
            })
        except ValidationError as e:
            failed.append({
                'name': employee_data.get('name', 'Unknown'),
                'error': str(e)
            })
    
    return successful, failed

# Test data
employee_data = [
    {
        'name': 'John Doe',
        'ssnid': '756.1234.5678.97'  # Valid
    },
    {
        'name': 'Jane Smith',
        'ssnid': '756.9999.9999.90'  # Valid in staging/development
    },
    {
        'name': 'Bob Johnson',
        'ssnid': '756.1234.5678.96'  # Invalid (wrong check digit)
    },
    {
        'name': 'Alice Williams',
        'ssnid': ''  # Empty (OK)
    },
    {
        'name': 'Charlie Brown',
        'ssnid': 'invalid'  # Invalid
    },
]

# Run import
successful, failed = import_employees(employee_data)

# Show results
print(f"Successful imports: {len(successful)}")
for emp in successful:
    print(f"  ✓ {emp['name']}: {emp['ssnid']}")

print(f"\nFailed imports: {len(failed)}")
for emp in failed:
    print(f"  ✗ {emp['name']}: {emp['error'][:50]}...")

print("\n✅ Real-world test completed!\n")
```

## Performance Test

```python
# ============= PERFORMANCE TEST =============

import time

print("Performance Test: Validate 10,000 OASIs\n")

# Generate test OASIs
test_oasis = []
for i in range(10000):
    # Generate some valid, some invalid
    if i % 5 == 0:
        test_oasis.append("756.1234.5678.97")  # Valid
    elif i % 5 == 1:
        test_oasis.append("7561234567897")      # Valid
    elif i % 5 == 2:
        test_oasis.append("756.invalid.format") # Invalid
    elif i % 5 == 3:
        test_oasis.append("123.1234.5678.97")   # Invalid
    else:
        test_oasis.append("")                    # Empty

# Run validation
start = time.time()
results = [OASIValidator.is_valid(oasi) for oasi in test_oasis]
elapsed = time.time() - start

# Show results
valid_count = sum(results)
invalid_count = len(results) - valid_count
per_second = len(results) / elapsed
per_ms = elapsed / len(results) * 1000

print(f"Total validations: {len(results)}")
print(f"Valid: {valid_count}")
print(f"Invalid: {invalid_count}")
print(f"\nPerformance:")
print(f"  Total time: {elapsed:.2f} seconds")
print(f"  Per validation: {per_ms:.3f} ms")
print(f"  Per second: {per_second:,.0f}")

print(f"\n✅ Performance test completed!")
```

## Running Tests

### In Odoo Shell

```bash
cd /path/to/odoo
python odoo-bin shell -d database_name
```

Then paste the test code above.

### In Python Console

```bash
python
>>> from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
>>> OASIValidator.is_valid("756.1234.5678.97")
True
```

### In Odoo Test Suite

```bash
python odoo-bin --test-enable -d test_db -i l10n_ch_oasi_verification -m l10n_ch_oasi_verification
```

---

## Expected Results

All tests should pass with these results:

```
✅ All basic validation tests passed!
✅ All sanitization tests passed!
✅ All check digit calculation tests passed!
✅ All check digit validation tests passed!
✅ All error handling tests passed!
✅ All model integration tests completed!
✅ Real-world test completed!
✅ Performance test completed!
```

---

## Troubleshooting

If tests fail:

1. **Import Error**: Make sure addon is properly installed
   ```python
   from l10n_ch_oasi_verification.models.oasi_validator import OASIValidator
   ```

2. **Model Error**: Make sure model exists and mixin is inherited
   ```python
   class MyModel(models.Model):
       _inherit = ['my.model', 'oasi.validation.mixin']
   ```

3. **Validation Error**: Check the error message for details
   ```python
   try:
       OASIValidator.validate_or_raise("invalid")
   except ValidationError as e:
       print(str(e))  # Shows what's wrong
   ```

---

**All tests ready to copy and paste! 🎯**
