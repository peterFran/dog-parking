import json
import os
import yaml


def load_openapi_spec():
    """
    Load OpenAPI specification from openapi.yaml file.
    The file is copied to the Lambda deployment package.
    """
    # Try to load from the Lambda package (root of the function)
    openapi_path = os.path.join(os.path.dirname(__file__), 'openapi.yaml')
    
    if os.path.exists(openapi_path):
        with open(openapi_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Fallback: Return a minimal spec if file not found
        return {
            "openapi": "3.0.1",
            "info": {
                "title": "Dog Care API",
                "version": "1.0.0",
                "description": "OpenAPI specification file not found. Please ensure openapi.yaml is included in deployment.",
            },
            "paths": {}
        }


def lambda_handler(event, context):
    """
    Documentation endpoint that serves OpenAPI spec from openapi.yaml and Swagger UI
    """
    path = event.get("path", "")
    http_method = event.get("httpMethod", "GET")
    
    # Load the OpenAPI spec from file
    openapi_spec = load_openapi_spec()
    
    # Update servers URL to match current deployment
    host = event.get("headers", {}).get("Host", "")
    stage = event.get("requestContext", {}).get("stage", "")
    
    if host and stage:
        openapi_spec["servers"] = [
            {
                "url": f"https://{host}/{stage}",
                "description": f"Current environment ({stage})"
            }
        ]
    
    # Serve OpenAPI spec as JSON
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
                url: 'https://{host}/{stage}/openapi.json',
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
                        "swagger_ui": f"https://{host}/{stage}/docs",
                        "openapi_spec": f"https://{host}/{stage}/openapi.json",
                    },
                }
            ),
        }
