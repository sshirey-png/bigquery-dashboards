"""
Simple web server to host the SR2/PMAP2 dashboard locally
Share the URL with your team on the same network
"""

import http.server
import socketserver
import socket

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Connect to an external host to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def serve(port=8080):
    """Start a simple HTTP server."""

    Handler = http.server.SimpleHTTPRequestHandler

    print("=" * 60)
    print("SR2/PMAP2 Dashboard Server")
    print("=" * 60)
    print()

    with socketserver.TCPServer(("", port), Handler) as httpd:
        local_ip = get_local_ip()

        print(f"Dashboard server is running!")
        print()
        print(f"Access the dashboard at:")
        print(f"  - On this computer: http://localhost:{port}")
        print(f"  - On your network:  http://{local_ip}:{port}")
        print()
        print("Share the network URL with your team members.")
        print("They can access it from any device on the same network.")
        print()
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        print()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")

if __name__ == "__main__":
    serve()
