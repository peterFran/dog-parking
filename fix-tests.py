#!/usr/bin/env python3

"""
Fix test files by simplifying DynamoDB table creation and removing unused variables
"""

import os
import re

def fix_test_file(filepath):
    """Fix a single test file"""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove unused imports
    content = re.sub(r'^import pytest\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^from datetime import datetime, timezone\n', '', content, flags=re.MULTILINE)
    
    # Fix unused variables by removing them
    content = re.sub(r'(\w+)_table = dynamodb\.create_table\(', r'dynamodb.create_table(', content)
    
    # Remove GSI BillingMode issues
    content = re.sub(r'"BillingMode": "PAY_PER_REQUEST",?\n\s*', '', content)
    
    # Remove OnDemandThroughput as it's not supported in moto
    content = re.sub(r'"OnDemandThroughput": \{[^}]+\},?\n\s*', '', content)
    
    # Move imports to top
    lines = content.split('\n')
    import_lines = []
    other_lines = []
    found_first_import = False
    
    for line in lines:
        if line.startswith('import ') or line.startswith('from '):
            if not found_first_import:
                found_first_import = True
            import_lines.append(line)
        elif line.startswith('# Add the functions'):
            # This is the start of path manipulation
            other_lines.extend(import_lines)
            import_lines = []
            other_lines.append(line)
        else:
            if found_first_import and import_lines:
                other_lines.extend(import_lines)
                import_lines = []
                found_first_import = False
            other_lines.append(line)
    
    content = '\n'.join(other_lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

# Fix all test files
test_files = [
    'tests/unit/test_dog_management.py',
    'tests/unit/test_owner_management.py', 
    'tests/unit/test_booking_management.py',
    'tests/unit/test_payment_processing.py'
]

for test_file in test_files:
    if os.path.exists(test_file):
        fix_test_file(test_file)

print("All test files fixed!")