import socket
import struct

def _ip_to_bytes(ip):
    return bytes(int(x) for x in ip.split('.'))

# mDNS multicast address and port
MDNS_ADDR = '224.0.0.251'
MDNS_PORT = 5353

def make_mdns_response(name, ip):
    """Craft a minimal mDNS A record response"""
    # Encode name like 'mini-soul' -> \x09mini-soul\x05local\x00
    parts = (name + '.local').split('.')
    encoded = b''
    for part in parts:
        encoded += bytes([len(part)]) + part.encode()
    encoded += b'\x00'

    ip_bytes = bytes(int(x) for x in ip.split('.'))

    # DNS response packet
    packet = (
        b'\x00\x00'          # Transaction ID
        b'\x84\x00'          # Flags: response, authoritative
        b'\x00\x00'          # Questions: 0
        b'\x00\x01'          # Answers: 1
        b'\x00\x00\x00\x00'  # Authority/Additional: 0
        + encoded
        + b'\x00\x01'        # Type: A
        + b'\x80\x01'        # Class: IN, cache-flush
        + b'\x00\x00\x00\x78'  # TTL: 120 seconds
        + b'\x00\x04'        # Data length: 4
        + ip_bytes
    )
    return packet

def start_mdns(hostname, ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MDNS_PORT))

    # Join multicast group
    mreq = _ip_to_bytes(MDNS_ADDR) + _ip_to_bytes('0.0.0.0')
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f'mDNS listening for {hostname}.local queries...')

    while True:
        data, addr = sock.recvfrom(512)
        # Check if query contains our hostname
        if hostname.encode() in data:
            response = make_mdns_response(hostname, ip)
            sock.sendto(response, (MDNS_ADDR, MDNS_PORT))
            print(f'Answered mDNS query from {addr}')


async def run_mdns(hostname, ip):
    """Async-friendly mDNS responder using a non-blocking socket."""
    import uasyncio as asyncio

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MDNS_PORT))

    mreq = _ip_to_bytes(MDNS_ADDR) + _ip_to_bytes('0.0.0.0')
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setblocking(False)

    print(f'mDNS: advertising {hostname}.local -> {ip}')

    while True:
        try:
            data, addr = sock.recvfrom(512)
            if hostname.encode() in data:
                response = make_mdns_response(hostname, ip)
                sock.sendto(response, (MDNS_ADDR, MDNS_PORT))
                print(f'mDNS: answered query from {addr}')
        except OSError:
            pass
        await asyncio.sleep(0.1)
