import json
import os
import logging
from datetime import datetime, timezone
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
import requests
from functools import wraps
from typing import Dict, Optional, Any
from cryptography import x509
from cryptography.hazmat.primitives import serialization

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Google's public keys endpoint
GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

# Cache for Google's public keys
_google_keys_cache = {}
_cache_expiry = None


def get_google_public_keys():
    """Fetch and cache Google's public keys for JWT verification"""
    global _google_keys_cache, _cache_expiry

    # Check cache validity (refresh every hour)
    if _cache_expiry and datetime.now(timezone.utc) < _cache_expiry:
        return _google_keys_cache

    try:
        response = requests.get(GOOGLE_CERTS_URL, timeout=10)
        response.raise_for_status()

        _google_keys_cache = response.json()
        # Cache for 1 hour
        _cache_expiry = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour + 1, minute=0, second=0, microsecond=0
        )

        return _google_keys_cache
    except Exception as e:
        logger.error(f"Failed to fetch Google public keys: {str(e)}")
        return {}


def verify_firebase_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase JWT token and extract claims"""
    try:
        project_id = os.environ.get("GOOGLE_PROJECT_ID")
        logger.info(f"Verifying token for project: {project_id}")
        
        # Get Google's public keys
        public_keys = get_google_public_keys()

        if not public_keys:
            logger.error("No Google public keys available")
            return None

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")
        logger.info(f"Token key ID: {key_id}")

        if not key_id or key_id not in public_keys:
            logger.error(f"Invalid key ID: {key_id}, available keys: {list(public_keys.keys())}")
            return None

        # Get the public key certificate
        public_key_cert = public_keys[key_id]
        logger.info(f"Public key cert type: {type(public_key_cert)}")
        logger.info(f"Public key cert length: {len(public_key_cert)}")
        
        # Check if it's a valid PEM certificate
        if not public_key_cert.startswith('-----BEGIN'):
            logger.error(f"Invalid certificate format. Expected PEM, got: {public_key_cert[:50]}...")
            return None

        # Ensure the certificate has proper line breaks
        # Sometimes the certificate comes as a single line and needs to be reformatted
        if '\n' not in public_key_cert:
            # If no line breaks, it's likely a single-line certificate that needs formatting
            lines = []
            cert_content = public_key_cert.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace(' ', '')
            
            lines.append('-----BEGIN CERTIFICATE-----')
            # Split into 64-character lines
            for i in range(0, len(cert_content), 64):
                lines.append(cert_content[i:i+64])
            lines.append('-----END CERTIFICATE-----')
            
            public_key_cert = '\n'.join(lines)
            logger.info("Reformatted certificate with proper line breaks")

        try:
            # Parse the certificate and extract the public key
            cert = x509.load_pem_x509_certificate(public_key_cert.encode('utf-8'))
            public_key = cert.public_key()
            
            # Convert to PEM format for PyJWT
            public_key_pem = public_key.public_key_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            logger.info("Successfully extracted public key from certificate")
            
            # Verify and decode token
            decoded_token = jwt.decode(
                token,
                public_key_pem,
                algorithms=["RS256"],
                audience=project_id,
                issuer=f"https://securetoken.google.com/{project_id}",
            )
        except Exception as decode_error:
            logger.error(f"JWT decode error: {str(decode_error)}")
            logger.error(f"Token preview: {token[:50]}...")
            logger.error(f"Audience: {project_id}")
            logger.error(f"Issuer: https://securetoken.google.com/{project_id}")
            # Log a few lines of the certificate for debugging (without exposing the full cert)
            cert_lines = public_key_cert.split('\n')
            logger.error(f"Certificate format check - Lines: {len(cert_lines)}")
            logger.error(f"First line: {cert_lines[0] if cert_lines else 'None'}")
            logger.error(f"Last line: {cert_lines[-1] if cert_lines else 'None'}")
            raise

        # Extract claims we need (no PII)
        claims = {
            "user_id": decoded_token.get("sub"),  # Google user ID (not PII)
            "email_verified": decoded_token.get("email_verified", False),
            "auth_time": decoded_token.get("auth_time"),
            "iat": decoded_token.get("iat"),
            "exp": decoded_token.get("exp"),
            "provider": decoded_token.get("firebase", {}).get(
                "sign_in_provider", "unknown"
            ),
        }

        # Add custom claims if present
        if "custom_claims" in decoded_token:
            claims["custom_claims"] = decoded_token["custom_claims"]

        logger.info(f"Token verified for user: {claims['user_id']}")
        return claims

    except ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except DecodeError:
        logger.error("Invalid token format")
        return None
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None


def extract_token_from_event(event: Dict[str, Any]) -> Optional[str]:
    """Extract JWT token from Lambda event"""
    # Check Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove 'Bearer ' prefix

    # Check query parameters
    query_params = event.get("queryStringParameters") or {}
    if "token" in query_params:
        return query_params["token"]

    return None


def require_auth(handler_func):
    """Decorator to require authentication for Lambda functions"""

    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        # Extract event from arguments - look through all arguments to find the Lambda event
        event = None
        for arg in args:
            if isinstance(arg, dict) and ('httpMethod' in arg or 'requestContext' in arg or 'headers' in arg):
                event = arg
                break
        
        if not event:
            logger.error(f"Could not find event in function arguments. Args: {len(args)}, Types: {[type(arg).__name__ for arg in args]}")
            return create_response(500, {"error": "Authentication service error"})
        
        try:
            # Extract token
            token = extract_token_from_event(event)

            if not token:
                return create_response(
                    401,
                    {
                        "error": "Missing authentication token",
                        "message": "Include Bearer token in Authorization header",
                    },
                )

            # Verify token
            claims = verify_firebase_token(token)

            if not claims:
                return create_response(
                    401,
                    {
                        "error": "Invalid authentication token",
                        "message": "Token verification failed",
                    },
                )

            # Add claims to event context
            event["auth_claims"] = claims

            # Call original handler with all arguments
            return handler_func(*args, **kwargs)

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return create_response(500, {"error": "Authentication service error"})

    return wrapper


def optional_auth(handler_func):
    """Decorator for optional authentication (adds claims if token present)"""

    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        # Extract event from arguments - look through all arguments to find the Lambda event
        event = None
        for arg in args:
            if isinstance(arg, dict) and ('httpMethod' in arg or 'requestContext' in arg or 'headers' in arg):
                event = arg
                break
        
        try:
            if event:
                # Extract token
                token = extract_token_from_event(event)

                if token:
                    # Verify token if present
                    claims = verify_firebase_token(token)
                    if claims:
                        event["auth_claims"] = claims

            # Call original handler (with or without claims)
            return handler_func(*args, **kwargs)

        except Exception as e:
            logger.error(f"Optional authentication error: {str(e)}")
            # Continue without auth on error
            return handler_func(*args, **kwargs)

    return wrapper


def get_user_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """Get user ID from authenticated event"""
    claims = event.get("auth_claims", {})
    return claims.get("user_id")


def is_user_verified(event: Dict[str, Any]) -> bool:
    """Check if user's email is verified"""
    claims = event.get("auth_claims", {})
    return claims.get("email_verified", False)


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        },
        "body": json.dumps(body),
    }


# Lambda handler for testing auth
def lambda_handler(event, context):
    """Test endpoint for authentication"""

    @require_auth
    def protected_endpoint(event, context):
        claims = event.get("auth_claims", {})
        return create_response(
            200,
            {
                "message": "Authentication successful",
                "user_id": claims.get("user_id"),
                "email_verified": claims.get("email_verified"),
                "provider": claims.get("provider"),
            },
        )

    return protected_endpoint(event, context)
