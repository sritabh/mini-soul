import network
import socket

# Create hotspot
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="MiniSoul", password="myminisoul", authmode=3)

while not ap.active():
    pass

print("Hotspot started:", ap.ifconfig())

# HTTP server
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("Listening on port 80...")

while True:
    conn, addr = s.accept()
    print("Connection from:", addr)
    request = conn.recv(1024)

    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Hello from Mini Soul!</h1>"
    conn.send(response)
    conn.close()
