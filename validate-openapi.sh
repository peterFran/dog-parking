#!/bin/bash
# Validate OpenAPI specification

set -e

echo "🔍 Validating OpenAPI specification..."

# Check if openapi-spec-validator is installed
if ! python3 -c "import openapi_spec_validator" 2>/dev/null; then
    echo "📦 Installing openapi-spec-validator..."
    pip install openapi-spec-validator==0.7.1
fi

# Validate the OpenAPI spec
python3 << 'EOF'
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename
import sys

try:
    spec_dict, spec_url = read_from_filename('openapi.yaml')
    validate_spec(spec_dict)
    print("✅ OpenAPI specification is valid!")

    # Print some stats
    paths = spec_dict.get('paths', {})
    schemas = spec_dict.get('components', {}).get('schemas', {})

    print(f"\n📊 Specification Statistics:")
    print(f"   • Endpoints: {len(paths)}")
    print(f"   • HTTP Operations: {sum(len(methods) for methods in paths.values())}")
    print(f"   • Schemas: {len(schemas)}")
    print(f"   • API Version: {spec_dict.get('info', {}).get('version', 'N/A')}")

    sys.exit(0)
except Exception as e:
    print(f"❌ OpenAPI specification is invalid!")
    print(f"   Error: {str(e)}")
    sys.exit(1)
EOF
