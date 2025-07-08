# Local Development Guide

## Quick Start (Recommended)

### 1. Start with SAM Local
```bash
# Terminal 1: Start DynamoDB Local
./setup-local-db.sh

# Terminal 2: Start API Gateway + Lambda
./start-local.sh
```

### 2. Test the API
```bash
# Test all endpoints
./test-api.sh

# Test specific endpoint
curl -X POST http://localhost:3000/owners/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@test.com","phone":"+1234567890"}'
```

## Alternative: Simple Server
If you want to avoid Docker/SAM:
```bash
# Start simple HTTP server
python3 run-simple-server.py

# Test with different port
./test-api.sh http://localhost:8080
```

## Development Workflow

### 1. Make Code Changes
Edit files in `functions/*/app.py`

### 2. Test Changes
```bash
# Run unit tests
./run-tests.sh

# Or just specific tests
source venv/bin/activate
pytest tests/unit/test_dog_management.py -v
```

### 3. Test API Locally
```bash
# Restart SAM Local (picks up changes)
# Test with curl or Postman
./test-api.sh
```

## Debugging

### SAM Local Logs
- Lambda logs appear in the SAM Local terminal
- DynamoDB operations are logged
- Check `functions/*/app.py` for logger.info() statements

### Common Issues
1. **Port conflicts**: Kill existing processes on ports 3000, 8000
2. **Docker not running**: Start Docker Desktop
3. **AWS credentials**: Set dummy credentials for local development

### Useful Commands
```bash
# List DynamoDB tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Scan table contents
aws dynamodb scan --table-name dogs-local --endpoint-url http://localhost:8000

# Stop containers
docker stop dynamodb-local && docker rm dynamodb-local
```

## API Endpoints

### Owners
- `POST /owners/register` - Register new owner
- `GET /owners/profile?owner_id=xxx` - Get owner details
- `PUT /owners/profile?owner_id=xxx` - Update owner

### Dogs
- `POST /dogs` - Register new dog
- `GET /dogs?owner_id=xxx` - List owner's dogs

### Bookings
- `POST /bookings` - Create booking
- `GET /bookings?owner_id=xxx` - List owner's bookings
- `PUT /bookings/{id}` - Update booking
- `DELETE /bookings/{id}` - Cancel booking

### Payments
- `POST /payments` - Process payment
- `GET /payments/{id}` - Get payment details
- `GET /payments?booking_id=xxx` - List payments for booking

## Next Steps
1. **Add frontend** (React, Vue, etc.)
2. **Add authentication** (see ADDING_AUTH.md)
3. **Deploy to AWS** (see DEPLOYMENT.md)