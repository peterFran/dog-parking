# Dog Care App - Infrastructure Architecture

## MVP Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │────│   API Gateway   │────│   Lambda        │
│   (Web/Mobile)  │    │   (REST API)    │    │   Functions     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   DynamoDB      │
                                              │   Tables        │
                                              └─────────────────┘
```

## Core Services

### 1. API Gateway
- **Type**: REST API
- **Features**: CORS enabled, request validation, rate limiting
- **Endpoints**:
  - `/dogs` - Dog management
  - `/owners` - Owner management
  - `/bookings` - Parking/care bookings
  - `/payments` - Payment processing

### 2. Lambda Functions
- **Runtime**: Python 3.11
- **Memory**: 512MB (optimized for cost/performance)
- **Timeout**: 30 seconds
- **Functions**:
  - `dog-management` - CRUD operations for dogs
  - `owner-management` - CRUD operations for owners
  - `booking-management` - Handle parking bookings
  - `payment-processing` - Handle payments

### 3. DynamoDB Tables
- **Billing**: On-demand (pay-per-use)
- **Tables**:
  - `dogs-table` - Dog profiles and information
  - `owners-table` - Owner profiles and information
  - `bookings-table` - Parking/care bookings
  - `payments-table` - Payment records

### 4. Supporting Services
- **CloudWatch**: Logging and monitoring
- **IAM**: Fine-grained access control
- **AWS Secrets Manager**: API keys and sensitive data

## Domain Model

### Dog Entity
```json
{
  "id": "dog-{uuid}",
  "name": "Buddy",
  "breed": "Golden Retriever",
  "age": 3,
  "size": "large",
  "owner_id": "owner-{uuid}",
  "vaccination_status": "up-to-date",
  "special_needs": ["medication", "food-allergy"],
  "emergency_contact": "+1234567890",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Owner Entity
```json
{
  "id": "owner-{uuid}",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
  },
  "dogs": ["dog-{uuid}"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Booking Entity
```json
{
  "id": "booking-{uuid}",
  "dog_id": "dog-{uuid}",
  "owner_id": "owner-{uuid}",
  "service_type": "daycare",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T17:00:00Z",
  "status": "confirmed",
  "price": 45.00,
  "payment_id": "payment-{uuid}",
  "special_instructions": "Feed at 12pm",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

### Dogs
- `GET /dogs` - List all dogs for authenticated owner
- `POST /dogs` - Create new dog profile
- `GET /dogs/{id}` - Get specific dog
- `PUT /dogs/{id}` - Update dog profile
- `DELETE /dogs/{id}` - Delete dog profile

### Owners
- `GET /owners/profile` - Get owner profile
- `PUT /owners/profile` - Update owner profile
- `POST /owners/register` - Register new owner

### Bookings
- `GET /bookings` - List bookings for authenticated owner
- `POST /bookings` - Create new booking
- `GET /bookings/{id}` - Get specific booking
- `PUT /bookings/{id}` - Update booking
- `DELETE /bookings/{id}` - Cancel booking

### Payments
- `POST /payments` - Process payment
- `GET /payments/{id}` - Get payment details

## Security Model

### Authentication
- JWT tokens for API access
- API Gateway authorizers
- Owner-based data isolation

### Authorization
- Owners can only access their own data
- Admin endpoints for service management
- Rate limiting per user/IP

## Cost Estimation (Monthly)
- API Gateway: ~$10-20 (1M requests)
- Lambda: ~$5-15 (compute time)
- DynamoDB: ~$5-10 (on-demand)
- CloudWatch: ~$2-5 (logs/metrics)
- **Total**: ~$25-50/month for moderate usage

## Deployment Strategy
1. **Development**: Single AWS account, dev stage
2. **Staging**: Same account, staging stage
3. **Production**: Separate account (recommended)

## Monitoring & Alerts
- CloudWatch dashboards for key metrics
- Error rate alerts (>5%)
- Cost alerts ($50, $100 thresholds)
- Performance alerts (response time >2s)