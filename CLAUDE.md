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