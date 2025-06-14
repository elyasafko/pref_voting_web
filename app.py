import socket
from app import create_app

def find_free_port(start=5000, max_port=6000):
    for port in range(start, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise OSError("No free ports found")

app = create_app()

if __name__ == '__main__':
    port = find_free_port()
    print(f"Running on http://0.0.0.0:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)