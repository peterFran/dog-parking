# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a serverless dog care platform with two main components:
1. **Backend**: AWS serverless infrastructure (Lambda + DynamoDB + API Gateway) using Python 3.13
2. **Frontend**: Next.js 15.3.5 application with TypeScript, deployed to Vercel

The platform handles dog registration, bookings, payments, and venue management with Firebase authentication.

## Development Commands

### Backend (AWS Serverless)

**Local Development Setup:**
```bash
# Set up local DynamoDB and create tables
./setup-local-db.sh

# Start local API server (runs on localhost:3000)
./start-local.sh

# Test the API endpoints
./test-api.sh http://localhost:3000
```

**Testing:**
```bash
# Run comprehensive test suite with coverage
./run-tests.sh

# Run specific test types
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Code quality checks
black functions/ tests/         # Format code
flake8 functions/ tests/        # Lint code
mypy functions/                 # Type checking
```

**Integration Test Requirements:**
Integration tests MUST pass before any deployment or feature completion. The platform has two types of integration tests:

1. **Local Integration Tests** (`test_api_integration.py`):
   - Used for local development with authentication disabled
   - Runs against `sam local start-api`
   - Tests basic API functionality without Firebase authentication

2. **CI/CD Integration Tests** (`test_api_with_firebase_emulator.py`):
   - Used in GitHub Actions with Firebase Auth emulator
   - Tests complete authentication flow with emulated Firebase
   - Must pass for all deployments to staging/production
   - Requires Firebase emulator running on port 9099
   - Uses test environment configuration (ENVIRONMENT=test)

**Firebase Emulator Setup for Integration Tests:**
```bash
# Start Firebase emulator for integration testing
firebase emulators:start --only auth --project demo-dog-care

# Run integration tests with emulator
export FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
export API_BASE_URL=http://127.0.0.1:3000
export TEST_PROJECT_ID=demo-dog-care
pytest tests/integration/test_api_with_firebase_emulator.py -v
```

Integration tests validate end-to-end authentication flows and ensure proper Firebase JWT token verification in all environments.

**Deployment:**
```bash
# Deploy to AWS environment
./deploy.sh dev dog-care-app    # Development
./deploy.sh staging dog-care-app # Staging
./deploy.sh prod dog-care-app   # Production

# Validate SAM template
sam validate --template template.yaml

# View logs
sam logs -n DogManagementFunction --stack-name dog-care-app-dev
```

### Frontend (Next.js)

```bash
cd dog-parking-app

# Development
npm run dev                     # Start dev server (localhost:3000)

# Build and deployment
npm run build                   # Production build
npm run start                   # Production server
npm run lint                    # ESLint checking
```

## Architecture Overview

### Backend Structure

**Lambda Functions** (in `functions/` directory):
- `dog_management/` - Dog CRUD operations with owner verification
- `owner_management/` - User profiles and preferences (no PII storage)
- `booking_management/` - Service bookings with venue validation
- `venue_management/` - Venue operations and slot management
- `auth/` - Firebase JWT verification layer (shared via Lambda Layer)

**Key Backend Patterns:**
- All functions use Firebase authentication via `@require_auth` decorator
- User ID extracted from JWT tokens, not request parameters
- DynamoDB tables use GSI indexes for owner-based queries
- Environment variables distinguish between local/AWS endpoints
- Decimal serialization for JSON responses to handle DynamoDB Decimal types

**DynamoDB Tables:**
- `dogs-local/dogs-{env}` - Dog profiles with owner-index GSI
- `owners-local/owners-{env}` - User preferences (keyed by Firebase user_id)
- `bookings-local/bookings-{env}` - Bookings with owner-time-index GSI
- `venues-local/venues-{env}` - Venue management and availability

### Frontend Structure

**Next.js App** (in `dog-parking-app/` directory):
- Firebase authentication with social login
- TanStack Query for API state management
- Tailwind CSS for styling
- TypeScript throughout

### Authentication Architecture

The platform uses **Firebase Authentication** (not AWS Cognito):
- Social login (Google OAuth, Apple Sign-In)
- JWT tokens verified in Lambda functions via `auth.py` layer
- No KYC requirements - relies on physical verification at venues
- User IDs from Firebase are used as primary keys in DynamoDB

## Key Implementation Details

### Authentication Flow
1. Frontend: Firebase social login generates JWT token
2. API calls: JWT sent in Authorization header (`Bearer <token>`)
3. Lambda Layer: `functions/auth/auth.py` verifies Firebase JWT
4. Functions: Use `@require_auth` decorator and `get_user_id_from_event()`

### Local vs Production Environment
- **Local**: Uses DynamoDB Local (port 8000) and Firebase emulator
- **Production**: Uses AWS DynamoDB and production Firebase project
- Environment detection via `AWS_SAM_LOCAL` environment variable

### Data Model Patterns
- **Owner Management**: Firebase user_id as primary key, no PII stored
- **Dog Registration**: Dogs linked to Firebase user_id via owner_id field
- **Booking System**: Hour-based subscription model (£20/hour blocks)
- **Access Control**: QR code generation for venue entry with human verification

### Known Issues & Technical Debt
- Missing payment processing Lambda function (referenced but not implemented)
- DynamoDB GSI query syntax issues in some GET endpoints with query parameters
- Schema inconsistency between `user_id` and `owner_id` fields across functions
- Authentication disabled in local development for easy testing

### Testing Strategy
- **Unit Tests**: Mock AWS services using `moto` library
- **Integration Tests**: Test against local DynamoDB and API
- **Coverage Threshold**: 76% minimum (configurable in `run-tests.sh`)
- **API Testing**: Use `test-api.sh` for end-to-end workflow validation

### Business Model Context
- **Subscription Model**: Monthly hour blocks (5hr/£100, 10hr/£200, 20hr/£380)
- **Service Types**: daycare, boarding, grooming, walking, training
- **Employee Management**: Deliberately descoped for MVP (partnership model planned)
- **Venue Access**: QR code + employee verification system (no hardware access control)

## Development Workflow

1. **Backend Changes**: Modify Lambda functions in `functions/` directory
2. **Local Testing**: Use `./start-local.sh` and `./test-api.sh`
3. **Code Quality**: Run `./run-tests.sh` before commits
4. **Frontend Changes**: Work in `dog-parking-app/` directory with `npm run dev`
5. **Deployment**: Use `./deploy.sh` for backend, Vercel for frontend

The codebase prioritizes rapid iteration and AWS serverless best practices while maintaining clear separation between authentication, business logic, and data persistence layers.

## Development Best Practices (Claude-Specific)

### OpenAPI & Code Generation
- **OpenAPI spec location**: `openapi.yaml` (root directory)
- **Generated models**: `functions/shared/models/generated.py` (auto-generated via `./generate-models.sh`)
- **Validation**: Use Pydantic v2 models from generated.py for all request validation
- **DO NOT modify generated.py directly** - update openapi.yaml and regenerate
- **Regeneration command**: `./generate-models.sh` (uses datamodel-code-generator)

### Lambda Layer Dependencies
- **ModelsLayer** (`functions/shared/`): Contains Pydantic models - **DO NOT add pydantic to individual Lambda requirements.txt**
- **AuthLayer** (`functions/auth/`): Contains Firebase authentication utilities
- **Dependency principle**: If a package is in a shared layer, remove it from function-specific requirements.txt to avoid conflicts
- **Critical**: Never pin `pydantic-core` explicitly - let Pydantic manage its own dependencies

### Error Handling Patterns
- **Validation errors (Pydantic)**: Return HTTP 422 with formatted error messages
- **Business logic errors**: Return HTTP 400 with simple error messages
- **Format Pydantic errors** for user-friendliness:
  ```python
  error_messages = []
  for error in e.errors():
      field = error['loc'][0] if error['loc'] else 'field'
      msg = error['msg']
      error_messages.append(f"{field}: {msg}")
  return create_response(422, {"error": "; ".join(error_messages)})
  ```

### SAM Build & Deployment
- **Local build issues**: If SAM build fails locally, it will fail in CI - check dependency conflicts first
- **Common failure**: Dependency conflicts between layers and function requirements
- **Resolution strategy**: Use `pip-compile` or manual resolution, ensure no duplicate dependencies
- **Layer permissions**: Deploying new layers requires `lambda:PublishLayerVersion` IAM permission

### Testing & CI/CD
- **Always run `./run-tests.sh` before pushing** - it catches 90% of CI failures
- **Test assertion patterns**: When updating error formats, update test assertions to match
- **Status code conventions**: 422 for validation, 400 for business logic, 401 for auth, 404 for not found
- **CI debugging**: Use `gh run view <run-id> --log-failed` to quickly find errors
- **Integration test failures**: Often IAM permission issues - check CloudFormation events for "CREATE_FAILED"

### IAM & Permissions
- **GitHub Actions IAM user**: `github-actions-dog-parking`
- **Required permissions for layers**: `lambda:PublishLayerVersion`, `lambda:GetLayerVersion`, `lambda:DeleteLayerVersion`
- **Policy location**: `corrected-iam-policy.json` (not checked into git)
- **Pattern**: When adding new AWS resources, update IAM policy proactively

### Pydantic-Specific Gotchas
- **Date parsing**: Pydantic auto-parses ISO date strings to `datetime.date` objects - don't call `strptime()` again
- **Enum serialization**: Use `model_dump(mode='json')` to properly serialize enums to strings
- **Enum value extraction**: Use `enum_field.value` to get string value, but check with `hasattr(s, 'value')` for safety
- **Nested models**: Use `.model_dump(mode='json')` for nested Pydantic models (e.g., operating_hours)

### Common Pitfalls to Avoid
1. **Don't duplicate dependencies** between layers and functions
2. **Don't pin transitive dependencies** (like pydantic-core) - let the main package manage them
3. **Don't skip test updates** when changing error response formats
4. **Don't assume local test success = CI success** - different Python environments can have different dependency resolution
5. **Don't commit without running `./run-tests.sh`** - it's your safety net

### Code Generation Workflow
When updating API schemas:
1. Update `openapi.yaml` (root directory - **single source of truth**)
2. Run `./generate-models.sh` to regenerate Pydantic models
3. Run `./sync-openapi.sh` to copy spec to docs function (happens automatically during deploy)
4. Update Lambda functions to use new model fields
5. Update tests to match new validation behavior
6. Run `./run-tests.sh` to verify everything works
7. Commit all changes together (openapi.yaml + generated.py + function code + tests)

**Important**: Never edit `functions/docs/openapi.yaml` directly - it's auto-generated by `sync-openapi.sh`