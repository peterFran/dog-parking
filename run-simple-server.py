#!/usr/bin/env python3
"""
Simple HTTP server for local development without Docker/SAM
Uses in-memory storage instead of DynamoDB for quick testing
"""

import json
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions/dog_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions/owner_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions/booking_management'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions/payment_processing'))

# In-memory storage (for development only)
storage = {
    'dogs': {},
    'owners': {},
    'bookings': {},
    'payments': {}
}

class DogCareHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)
        
        if path.startswith('/owners/profile'):
            self.handle_owner_profile_get(params)
        elif path.startswith('/dogs'):
            self.handle_dogs_get(params)
        elif path.startswith('/bookings'):
            self.handle_bookings_get(params)
        elif path.startswith('/payments/'):
            payment_id = path.split('/')[-1]
            self.handle_payment_get(payment_id)
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        body = json.loads(post_data.decode('utf-8'))
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/owners/register':
            self.handle_owner_register(body)
        elif path == '/dogs':
            self.handle_dog_create(body)
        elif path == '/bookings':
            self.handle_booking_create(body)
        elif path == '/payments':
            self.handle_payment_create(body)
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_owner_register(self, body):
        owner_id = f"owner-{uuid.uuid4()}"
        owner = {
            'id': owner_id,
            'name': body['name'],
            'email': body['email'],
            'phone': body['phone'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        storage['owners'][owner_id] = owner
        self.send_json_response(201, owner)
    
    def handle_dog_create(self, body):
        dog_id = f"dog-{uuid.uuid4()}"
        dog = {
            'id': dog_id,
            'name': body['name'],
            'breed': body['breed'],
            'age': body['age'],
            'size': body['size'],
            'owner_id': body['owner_id'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        storage['dogs'][dog_id] = dog
        self.send_json_response(201, dog)
    
    def handle_booking_create(self, body):
        booking_id = f"booking-{uuid.uuid4()}"
        booking = {
            'id': booking_id,
            'dog_id': body['dog_id'],
            'owner_id': body['owner_id'],
            'service_type': body['service_type'],
            'start_time': body['start_time'],
            'end_time': body['end_time'],
            'status': 'pending',
            'price': 120.0,  # Simple calculation
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        storage['bookings'][booking_id] = booking
        self.send_json_response(201, booking)
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == '__main__':
    port = 8080
    server = HTTPServer(('localhost', port), DogCareHandler)
    print(f"🐕 Dog Care API running at http://localhost:{port}")
    print("Available endpoints:")
    print("  POST /owners/register")
    print("  POST /dogs")
    print("  POST /bookings")
    print("  POST /payments")
    print("\nPress Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.shutdown()