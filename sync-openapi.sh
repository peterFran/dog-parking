#!/bin/bash
# Sync openapi.yaml to docs function before SAM build
# This ensures we always have the latest version in the Lambda package

set -e

echo "📄 Syncing openapi.yaml to docs function..."
cp openapi.yaml functions/docs/openapi.yaml
echo "✅ OpenAPI spec synced successfully"
