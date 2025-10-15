# API Documentation Function

This Lambda function serves the OpenAPI specification and Swagger UI for the Dog Care API.

## OpenAPI Spec Management

**IMPORTANT**: The `openapi.yaml` file in this directory is **auto-generated** from the root `openapi.yaml`.

- **Source of truth**: `/openapi.yaml` (repository root)
- **Auto-copied to**: `/functions/docs/openapi.yaml` (this directory)
- **Copy happens**: Before every SAM build via `sync-openapi.sh` script

### Why this approach?

We need the OpenAPI spec available at runtime in the Lambda function, but we don't want to maintain two copies manually. The sync script ensures the docs function always has the latest version.

### Making Changes

1. **Edit** `/openapi.yaml` (repository root) - this is the source of truth
2. **Run** `./sync-openapi.sh` to copy to this directory
3. **Build** with `sam build` (or `./deploy.sh` which calls the sync script automatically)

### CI/CD

All GitHub Actions workflows automatically run `sync-openapi.sh` before building to ensure the docs function has the latest spec.

## Dependencies

- `pyyaml>=6.0` - For loading YAML files at runtime
