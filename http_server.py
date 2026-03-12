import network
import socket
try:
    import ujson as json
except ImportError:
    import json

# Create hotspot
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="MiniSoul", password="myminisoul", authmode=3)

while not ap.active():
    pass

print("Hotspot started:", ap.ifconfig())


def parse_request(data):
    sep = b'\r\n\r\n'
    sep_idx = data.find(sep)
    if sep_idx == -1:
        headers_raw, body = data, b''
    else:
        headers_raw, body = data[:sep_idx], data[sep_idx + 4:]
    first_line = headers_raw.decode('utf-8').split('\r\n')[0].split(' ')
    method = first_line[0] if first_line else 'GET'
    path = first_line[1] if len(first_line) > 1 else '/'
    return method, path, body


# HTTP server
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Listening on port 80...")

while True:
    conn, addr = s.accept()
    print("Connection from:", addr)
    request = conn.recv(4096)

    method, path, body = parse_request(request)
    print("Request:", method, path)

    if method == 'GET' and path == '/':
        try:
            with open('setup_ui/index.html', 'r') as f:
                html = f.read()
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: {}\r\n"
                "\r\n{}"
            ).format(len(html), html)
        except OSError:
            response = "HTTP/1.1 404 Not Found\r\nContent-Length: 14\r\n\r\nFile not found."
    elif method == 'POST' and path == '/save':
        try:
            data = json.loads(body)
            print("Received data:", data)
            resp_body = '{"status":"ok"}'
        except Exception as e:
            print("Error parsing body:", e)
            resp_body = '{"status":"error"}'
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "\r\n{}"
        ).format(len(resp_body), resp_body)
    else:
        response = "HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot found"

    conn.sendall(response.encode('utf-8'))
    conn.close()
