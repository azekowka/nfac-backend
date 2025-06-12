#!/usr/bin/env python3
"""
Simple HTTP server for A2A Chatbot Frontend
Serves static files with CORS support for development
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse, parse_qs

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Custom logging format
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=3000):
    """Run the HTTP server"""
    # Change to frontend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = CORSRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"\n🚀 A2A Chatbot Frontend Server")
            print(f"📁 Serving from: {os.getcwd()}")
            print(f"🌐 Local: http://localhost:{port}")
            print(f"🔗 Network: http://{get_local_ip()}:{port}")
            print(f"⚡ Backend: http://localhost:8102 (A2A Chatbot)")
            print(f"\n✨ Press Ctrl+C to stop the server\n")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print(f"💡 Try a different port: python server.py --port 3001")
        else:
            print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        # Connect to a dummy address to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='A2A Chatbot Frontend Server')
    parser.add_argument('--port', '-p', type=int, default=3000, 
                       help='Port number (default: 3000)')
    
    args = parser.parse_args()
    run_server(args.port) 