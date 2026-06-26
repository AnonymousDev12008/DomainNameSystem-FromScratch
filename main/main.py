import socket
import threading

from block import load_blocklist,is_blocked
from parser import parse_DNSPacket
from encoder import header_to_bytes, record_to_bytes, encode_dns_name
from models import DNSHeader, DNSRecord
from resolver import  resolve
import struct

def build_error_response(query_packet, error_type):
    if error_type == "NXDOMAIN":
        flags = 0x8183
    elif error_type == "SERVFAIL":
        flags = 0x8182
    else:
        flags = 0x8180  # NOERROR empty

    error_header = DNSHeader(
        id=query_packet.header.id,
        flags=flags,
        num_questions=1,
        num_answers=0
    )
    question = query_packet.questions[0]
    return (
            header_to_bytes(error_header) +
            encode_dns_name(question.name.decode("utf-8")) +
            struct.pack("!HH", question.type_, question.class_)
    )

def handle_query(data, addr, sock):
    try:
        query_packet = parse_DNSPacket(data)
        domain = query_packet.questions[0].name.decode("utf-8")
        record_type = query_packet.questions[0].type_
        print(f"query from {addr} for {domain}")

        if is_blocked(domain):
            print(f"blocked {domain}")
            response = build_error_response(query_packet, "NXDOMAIN")
            sock.sendto(response, addr)
            return

        ip = resolve(domain, record_type)

        if ip is None:
            response = build_error_response(query_packet, "NOERROR")
        elif ip == "NXDOMAIN":
            response = build_error_response(query_packet, "NXDOMAIN")
        else:
            response = build_response(query_packet, ip)

        sock.sendto(response, addr)

    except Exception as e:
        print(f"error handling query: {e}")
        try:
            response = build_error_response(query_packet, "SERVFAIL")
            sock.sendto(response, addr)
        except:
            pass

def build_response(query_packet, ip):
    response_header = DNSHeader(
        id=query_packet.header.id,
        flags=0x8180,
        num_questions=1,
        num_answers=1
    )
    answer = DNSRecord(
        name=b"\xc0\x0c",
        type_=query_packet.questions[0].type_,
        class_=1,
        ttl=300,
        data=ip
    )
    question = query_packet.questions[0]
    return (
            header_to_bytes(response_header) +
            encode_dns_name(question.name.decode("utf-8")) +
            struct.pack("!HH", question.type_, question.class_) +
            record_to_bytes(answer)
    )



def start_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 8035))
    print("DNS listener running on port 8035...")
    while True:
        data, addr = sock.recvfrom(1024)
        thread = threading.Thread(target=handle_query, args=(data, addr, sock))
        thread.daemon = True
        thread.start()

load_blocklist("blocklist.txt")
start_listener()