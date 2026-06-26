import dataclasses
from models import DNSHeader,DNSQuestion,DNSRecord
import struct
import random
import socket

TYPE_A=1
TYPE_NS=2
CLASS_IN=1
TYPE_AAAA=28
TYPE_CNAME=5

def header_to_bytes(header:DNSHeader):
    fields=dataclasses.astuple(header)
    return struct.pack("!HHHHHH",*fields)

def encode_dns_name(domain_name:str):
    if isinstance(domain_name, bytes):
        domain_name = domain_name.decode("utf-8")
    encoded=b""
    for part in domain_name.encode("ascii").split(b"."):
        encoded+=bytes([len(part)])+part
    return encoded+b"\x00"

def question_to_bytes(question:DNSQuestion):
    return question.name+struct.pack("!HH",question.type_,question.class_)

def record_to_bytes(record: DNSRecord):
    name = b"\xc0\x0c"

    if record.data is None:
        data = b""
    elif record.type_ == TYPE_A:
        data = socket.inet_aton(record.data if isinstance(record.data, str) else record.data.decode("utf-8"))
    elif record.type_ == TYPE_AAAA:
        data = socket.inet_pton(socket.AF_INET6, record.data if isinstance(record.data, str) else record.data.decode("utf-8"))
    elif record.type_ in (TYPE_NS, TYPE_CNAME):
        data = encode_dns_name(record.data.decode("utf-8") if isinstance(record.data, bytes) else record.data)
    else:
        data = record.data if isinstance(record.data, bytes) else record.data.encode("utf-8")

    return (
            name +
            struct.pack("!HHIH", record.type_, record.class_, record.ttl, len(data)) +
            data
    )

def build_query(domain_name,record_type):
    name=encode_dns_name(domain_name)
    id=random.randint(0,65535)
    "RECURSION_DESIRED=1 << 8"
    #recursion desired is the ninth bit from right so right shift 1 by 8 positions we land at 9 as per RFC 1035
    #this was stubbed earlier as I was kinda working with calling a resolver {trying to be a toy dns client} .
    header = DNSHeader(id=id,num_questions=1,flags=0)
    question=DNSQuestion(name=name,type_=record_type,class_=CLASS_IN)
    return header_to_bytes(header)+question_to_bytes(question)
