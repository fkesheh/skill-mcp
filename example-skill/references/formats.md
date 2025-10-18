# Data Formats Reference

This document describes the expected data formats for the data processor skill.

## CSV Format

### Basic Requirements

CSV files must:
- Have a header row with column names
- Use comma (,) as the delimiter
- Use double quotes (") for fields containing commas or newlines
- Be UTF-8 encoded

### Example Format

```csv
name,email,age,city
John Doe,john@example.com,30,New York
Jane Smith,jane@example.com,25,San Francisco
Bob Johnson,bob@example.com,35,Chicago
```

## Supported Column Types

### Text Columns
- Any string data
- Can contain spaces and special characters
- Quotes are automatically handled

### Numeric Columns
- Integers: 1, 42, -5
- Decimals: 3.14, -0.5, 1.234

### Date Columns
Supported formats:
- ISO 8601: 2024-01-15
- US Format: 01/15/2024
- Full: 2024-01-15 14:30:00

## Special Values

### Missing Data
Represented as:
- Empty field: ,,
- NULL text: ,NULL,
- NA text: ,NA,

### Boolean Values
- True: true, TRUE, 1, yes, YES
- False: false, FALSE, 0, no, NO

## File Size Limits

- Maximum file size: 100 MB
- Maximum rows: 1,000,000 (configurable via MAX_ROWS)
- Maximum columns: 1,000

## Common Issues

### Issue: "Invalid CSV format"
**Cause:** File is not properly formatted CSV  
**Solution:** Ensure file has comma delimiters and proper headers

### Issue: "Encoding error"
**Cause:** File is not UTF-8 encoded  
**Solution:** Convert file to UTF-8 encoding

### Issue: "Too many rows"
**Cause:** File exceeds MAX_ROWS limit  
**Solution:** Set MAX_ROWS environment variable higher or split the file
