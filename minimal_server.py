#!/usr/bin/env python3
"""Minimal working server"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir('/Users/marcdebrey/cpq-revenue-cloud-migration/POC')

print("Starting minimal server on http://localhost:8080")
print("This will serve files from the current directory")
print("Press Ctrl+C to stop\n")

# Use the built-in SimpleHTTPRequestHandler which definitely works
httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped")