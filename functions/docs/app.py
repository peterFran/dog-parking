import json
import os


def lambda_handler(event, context):
    """
    Simple documentation endpoint that serves OpenAPI spec and Swagger UI
    """
    path = event.get("path", "")
    http_method = event.get("httpMethod", "GET")

    # OpenAPI specification
    openapi_spec = {
        "openapi": "3.0.1",
        "info": {
            "title": "Dog Care API",
            "version": "1.0.0",
            "description": "API for managing dog care services, venues, and bookings. Uses Firebase authentication for user management.",
        },
        "servers": [
            {
                "url": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}",
                "description": "Current environment",
            }
        ],
        "components": {
            "securitySchemes": {
                "FirebaseAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Firebase ID token. Include as 'Authorization: Bearer <token>' header."
                }
            },
            "responses": {
                "UnauthorizedError": {
                    "description": "Authentication token missing or invalid",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "message": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "ForbiddenError": {
                    "description": "Access denied - insufficient permissions",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "paths": {
            "/owners/register": {
                "post": {
                    "summary": "Register a new owner profile",
                    "description": "Creates owner profile using authenticated user ID. Requires verified email.",
                    "security": [{"FirebaseAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "preferences": {
                                            "type": "object",
                                            "properties": {
                                                "notifications": {"type": "boolean"},
                                                "marketing_emails": {"type": "boolean"},
                                                "preferred_communication": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Owner profile created successfully"},
                        "400": {"description": "Invalid input or email not verified"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }
            },
            "/owners/profile": {
                "get": {
                    "summary": "Get authenticated user's profile",
                    "description": "Retrieves profile for authenticated user. Creates basic profile if doesn't exist.",
                    "security": [{"FirebaseAuth": []}],
                    "responses": {
                        "200": {"description": "Owner profile retrieved"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                },
                "put": {
                    "summary": "Update authenticated user's profile",
                    "description": "Updates profile preferences for authenticated user.",
                    "security": [{"FirebaseAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "preferences": {"type": "object"},
                                        "notification_settings": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Profile updated successfully"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                }
            },
            "/venues": {
                "get": {
                    "summary": "List all venues",
                    "responses": {"200": {"description": "List of venues"}},
                },
                "post": {
                    "summary": "Create a new venue",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "name",
                                        "address",
                                        "capacity",
                                        "operating_hours",
                                    ],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "address": {"type": "object"},
                                        "capacity": {"type": "integer", "minimum": 1},
                                        "operating_hours": {"type": "object"},
                                        "services": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "slot_duration": {
                                            "type": "integer",
                                            "default": 60,
                                        },
                                    },
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Venue created successfully"},
                        "400": {"description": "Invalid input"},
                    },
                },
            },
            "/venues/{id}": {
                "get": {
                    "summary": "Get venue details",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue details"},
                        "404": {"description": "Venue not found"},
                    },
                },
                "put": {
                    "summary": "Update venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue updated"},
                        "404": {"description": "Venue not found"},
                    },
                },
                "delete": {
                    "summary": "Delete venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue deleted"},
                        "404": {"description": "Venue not found"},
                    },
                },
            },
            "/venues/{id}/slots": {
                "get": {
                    "summary": "Get available slots for a venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "date",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "date"},
                            "description": "Date in YYYY-MM-DD format",
                        },
                    ],
                    "responses": {
                        "200": {"description": "Available slots"},
                        "400": {"description": "Invalid date format"},
                        "404": {"description": "Venue not found"},
                    },
                }
            },
            "/dogs": {
                "get": {
                    "summary": "List dogs for authenticated user",
                    "description": "Returns all dogs owned by the authenticated user.",
                    "security": [{"FirebaseAuth": []}],
                    "responses": {
                        "200": {"description": "List of dogs"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                },
                "post": {
                    "summary": "Register a new dog",
                    "description": "Creates a new dog for the authenticated user. Requires owner profile to exist.",
                    "security": [{"FirebaseAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "breed", "date_of_birth", "size", "vaccination_status"],
                                    "properties": {
                                        "name": {"type": "string", "description": "Dog's name"},
                                        "breed": {"type": "string", "description": "Dog's breed"},
                                        "date_of_birth": {"type": "string", "format": "date", "description": "Date of birth in YYYY-MM-DD format. Age will be calculated automatically."},
                                        "size": {
                                            "type": "string",
                                            "enum": ["SMALL", "MEDIUM", "LARGE", "XLARGE"],
                                            "description": "Dog size category"
                                        },
                                        "vaccination_status": {
                                            "type": "string",
                                            "enum": ["VACCINATED", "NOT_VACCINATED"],
                                            "description": "Vaccination status"
                                        },
                                        "microchipped": {"type": "boolean", "description": "Whether the dog is microchipped (default: false)"},
                                        "special_needs": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Array of special needs or medical requirements"
                                        },
                                        "medical_notes": {"type": "string", "description": "Medical notes and health information"},
                                        "behavior_notes": {"type": "string", "description": "Behavioral notes and temperament information"},
                                        "favorite_activities": {"type": "string", "description": "Comma-separated list of favorite activities"}
                                    },
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Dog registered successfully"},
                        "400": {"description": "Invalid input or owner profile not found"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                },
            },
            "/dogs/{id}": {
                "get": {
                    "summary": "Get specific dog",
                    "description": "Returns dog details. Only accessible by dog owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Dog details"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Dog not found"},
                    },
                },
                "put": {
                    "summary": "Update dog",
                    "description": "Updates dog information. Only accessible by dog owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Dog's name"},
                                        "breed": {"type": "string", "description": "Dog's breed"},
                                        "size": {
                                            "type": "string",
                                            "enum": ["SMALL", "MEDIUM", "LARGE", "XLARGE"],
                                            "description": "Dog size category"
                                        },
                                        "vaccination_status": {
                                            "type": "string",
                                            "enum": ["VACCINATED", "NOT_VACCINATED"],
                                            "description": "Vaccination status"
                                        },
                                        "microchipped": {"type": "boolean", "description": "Whether the dog is microchipped"},
                                        "special_needs": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Array of special needs or medical requirements"
                                        },
                                        "medical_notes": {"type": "string", "description": "Medical notes and health information"},
                                        "behavior_notes": {"type": "string", "description": "Behavioral notes and temperament information"},
                                        "favorite_activities": {"type": "string", "description": "Comma-separated list of favorite activities"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Dog updated successfully"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Dog not found"},
                    },
                },
                "delete": {
                    "summary": "Delete dog",
                    "description": "Deletes dog. Only accessible by dog owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "204": {"description": "Dog deleted successfully"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Dog not found"},
                    },
                },
            },
            "/bookings": {
                "get": {
                    "summary": "List bookings for authenticated user",
                    "description": "Returns all bookings for the authenticated user.",
                    "security": [{"FirebaseAuth": []}],
                    "responses": {
                        "200": {"description": "List of bookings"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                    },
                },
                "post": {
                    "summary": "Create a new booking",
                    "description": "Creates a booking for the authenticated user. Dog must belong to user.",
                    "security": [{"FirebaseAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "dog_id",
                                        "venue_id",
                                        "service_type",
                                        "start_time",
                                        "end_time",
                                    ],
                                    "properties": {
                                        "dog_id": {"type": "string"},
                                        "venue_id": {"type": "string"},
                                        "service_type": {
                                            "type": "string",
                                            "enum": [
                                                "daycare",
                                                "boarding",
                                                "grooming",
                                                "walking",
                                                "training",
                                            ],
                                        },
                                        "start_time": {
                                            "type": "string",
                                            "format": "date-time",
                                        },
                                        "end_time": {
                                            "type": "string",
                                            "format": "date-time",
                                        },
                                        "special_instructions": {"type": "string"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Booking created successfully"},
                        "400": {"description": "Invalid input or validation failed"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"description": "Dog does not belong to this owner"},
                        "404": {"description": "Dog, venue, or owner profile not found"},
                    },
                },
            },
            "/bookings/{id}": {
                "get": {
                    "summary": "Get specific booking",
                    "description": "Returns booking details. Only accessible by booking owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Booking details"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Booking not found"},
                    },
                },
                "put": {
                    "summary": "Update booking",
                    "description": "Updates booking information. Only accessible by booking owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "enum": ["pending", "confirmed", "cancelled"]
                                        },
                                        "special_instructions": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Booking updated successfully"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Booking not found"},
                    },
                },
                "delete": {
                    "summary": "Cancel booking",
                    "description": "Cancels booking. Only accessible by booking owner.",
                    "security": [{"FirebaseAuth": []}],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Booking cancelled successfully"},
                        "401": {"$ref": "#/components/responses/UnauthorizedError"},
                        "403": {"$ref": "#/components/responses/ForbiddenError"},
                        "404": {"description": "Booking not found"},
                    },
                },
            },
        },
    }

    # Serve OpenAPI spec
    if path.endswith("/openapi.json"):
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(openapi_spec),
        }

    # Serve Swagger UI
    elif path.endswith("/docs") or path.endswith("/docs/"):
        swagger_ui_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dog Care API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin:0; background: #fafafa; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: 'https://{event.get("headers", {}).get("Host", "")}/{event.get("requestContext", {}).get("stage", "")}/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>"""
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html",
                "Access-Control-Allow-Origin": "*",
            },
            "body": swagger_ui_html,
        }

    # Default response with links
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Dog Care API Documentation",
                    "endpoints": {
                        "swagger_ui": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}/docs",
                        "openapi_spec": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}/openapi.json",
                    },
                }
            ),
        }
