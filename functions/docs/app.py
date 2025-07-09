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
            "description": "API for managing dog care services, venues, and bookings"
        },
        "servers": [
            {
                "url": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}",
                "description": "Current environment"
            }
        ],
        "paths": {
            "/owners/register": {
                "post": {
                    "summary": "Register a new owner",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "email", "phone"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string", "format": "email"},
                                        "phone": {"type": "string"},
                                        "address": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Owner registered successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/owners/profile": {
                "get": {
                    "summary": "Get owner profile",
                    "parameters": [
                        {
                            "name": "owner_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Owner profile retrieved"},
                        "404": {"description": "Owner not found"}
                    }
                }
            },
            "/venues": {
                "get": {
                    "summary": "List all venues",
                    "responses": {
                        "200": {"description": "List of venues"}
                    }
                },
                "post": {
                    "summary": "Create a new venue",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "address", "capacity", "operating_hours"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "address": {"type": "object"},
                                        "capacity": {"type": "integer", "minimum": 1},
                                        "operating_hours": {"type": "object"},
                                        "services": {"type": "array", "items": {"type": "string"}},
                                        "slot_duration": {"type": "integer", "default": 60}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Venue created successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/venues/{id}": {
                "get": {
                    "summary": "Get venue details",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue details"},
                        "404": {"description": "Venue not found"}
                    }
                },
                "put": {
                    "summary": "Update venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue updated"},
                        "404": {"description": "Venue not found"}
                    }
                },
                "delete": {
                    "summary": "Delete venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Venue deleted"},
                        "404": {"description": "Venue not found"}
                    }
                }
            },
            "/venues/{id}/slots": {
                "get": {
                    "summary": "Get available slots for a venue",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "date",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "date"},
                            "description": "Date in YYYY-MM-DD format"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Available slots"},
                        "400": {"description": "Invalid date format"},
                        "404": {"description": "Venue not found"}
                    }
                }
            },
            "/dogs": {
                "get": {
                    "summary": "List dogs for an owner",
                    "parameters": [
                        {
                            "name": "owner_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "List of dogs"}
                    }
                },
                "post": {
                    "summary": "Register a new dog",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "breed", "age", "size", "owner_id"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "breed": {"type": "string"},
                                        "age": {"type": "integer", "minimum": 0},
                                        "size": {"type": "string", "enum": ["small", "medium", "large"]},
                                        "owner_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Dog registered successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            },
            "/bookings": {
                "get": {
                    "summary": "List bookings for an owner",
                    "parameters": [
                        {
                            "name": "owner_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "List of bookings"}
                    }
                },
                "post": {
                    "summary": "Create a new booking",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["dog_id", "owner_id", "venue_id", "service_type", "start_time", "end_time"],
                                    "properties": {
                                        "dog_id": {"type": "string"},
                                        "owner_id": {"type": "string"},
                                        "venue_id": {"type": "string"},
                                        "service_type": {"type": "string", "enum": ["daycare", "boarding", "grooming", "walking", "training"]},
                                        "start_time": {"type": "string", "format": "date-time"},
                                        "end_time": {"type": "string", "format": "date-time"},
                                        "special_instructions": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Booking created successfully"},
                        "400": {"description": "Invalid input"}
                    }
                }
            }
        }
    }
    
    # Serve OpenAPI spec
    if path.endswith("/openapi.json"):
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(openapi_spec)
        }
    
    # Serve Swagger UI
    elif path.endswith("/docs") or path.endswith("/docs/"):
        swagger_ui_html = f'''
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
                url: '{event.get("headers", {}).get("Host", "")}/{event.get("requestContext", {}).get("stage", "")}/openapi.json',
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
</html>'''
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html",
                "Access-Control-Allow-Origin": "*"
            },
            "body": swagger_ui_html
        }
    
    # Default response with links
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Dog Care API Documentation",
                "endpoints": {
                    "swagger_ui": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}/docs",
                    "openapi_spec": f"https://{event['headers']['Host']}/{event['requestContext']['stage']}/openapi.json"
                }
            })
        }