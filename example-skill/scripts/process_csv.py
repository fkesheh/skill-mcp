#!/usr/bin/env python3
"""
Example data processing script that uses environment variables.

This script demonstrates:
- Reading environment variables
- Processing CSV files
- Error handling
- Proper output
"""

import os
import sys
import csv
from pathlib import Path

def main():
    # Get environment variables
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    max_rows = int(os.environ.get('MAX_ROWS', '10000'))
    
    # Get input file from arguments
    if len(sys.argv) < 2:
        print("Usage: process_csv.py <input.csv>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check if file exists
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Max rows: {max_rows}")
    
    # Process the CSV
    try:
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:max_rows]
            
            print(f"\nProcessed {len(rows)} rows")
            print(f"Columns: {', '.join(reader.fieldnames)}")
            
            # Example: Count non-empty values per column
            print("\nData Summary:")
            for field in reader.fieldnames:
                non_empty = sum(1 for row in rows if row.get(field))
                print(f"  {field}: {non_empty}/{len(rows)} non-empty")
            
            print("\n✓ Processing complete!")
            
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
