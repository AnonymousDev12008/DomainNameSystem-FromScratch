from parser import parse_DNSPacket
import socket
from main.main.main import build_query

def send_query(ip_address, domain_name, record_type):
    query=build_query(domain_name, record_type)
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.sendto(query,(ip_address, 53))
    sock.settimeout(5)
    for attempt in range(3):  # retry up to 3 times
        try:
            sock.sendto(query, (ip_address, 53))
            data, _ = sock.recvfrom(1024)
            return parse_DNSPacket(data)
        except socket.timeout:
            print(f"timeout on {ip_address}, attempt {attempt + 1}/3")

    raise Exception(f"all retries failed for {ip_address}")

