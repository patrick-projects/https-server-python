import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

# Function to generate a self-signed certificate
def generate_self_signed_cert(cert_file, key_file):
    # Check if the certificate and key files already exist
    if not os.path.isfile(cert_file) or not os.path.isfile(key_file):
        # Generate self-signed certificate and key
        subprocess.call([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', key_file, '-out', cert_file,
            '-days', '365', '-nodes', '-subj', '/CN=localhost'
        ])

# File paths
certificate_file = "certificate.pem"
private_key_file = "privatekey.pem"

# Generate the self-signed certificate if needed
generate_self_signed_cert(certificate_file, private_key_file)

# Create a simple HTTP server
httpd = HTTPServer(('0.0.0.0', 443), SimpleHTTPRequestHandler)

# SSL context setup
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certificate_file, private_key_file)

# Wrap the httpd server socket into ssl
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

# Serve indefinitely
httpd.serve_forever()
