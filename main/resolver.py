from network import send_query
from cache import cache_get,cache_set
from utils import  RCODE_NXDOMAIN, get_rcode
from utils import is_noerror

NXDOMAIN_TTL=300
TYPE_A=1
TYPE_NS=2
TYPE_CNAME=5
CLASS_IN=1
TYPE_AAAA=28

def get_answer(packet,record_type):
    for x in packet.answers:
        if x.type_ == record_type:
            return x.data

def get_cname(packet):
    for x in packet.answers:
        if x.type_ == TYPE_CNAME:
            return x.data.decode('utf-8')

def get_nameserver_ip(packet):
    for x in packet.additionals:
        if x.type_ == TYPE_A:
            return x.data

def get_nameserver(packet):
    for x in packet.authorities:
        if x.type_ == TYPE_NS:
            return x.data.decode('utf-8')

def resolve(domain_name, record_type):
    if (data:=cache_get(domain_name, record_type)) is not None:
        return data
    else:
        nameserver="192.36.148.17"
        while True:
            print(f"Querying {nameserver} for {domain_name}")
            response = send_query(nameserver, domain_name, record_type)

            rcode = get_rcode(response.header.flags)
            if rcode == RCODE_NXDOMAIN:
                cache_set(domain_name, record_type, "NXDOMAIN", NXDOMAIN_TTL)
                return "NXDOMAIN"

            if ip := get_answer(response, record_type):
                cache_set(domain_name, record_type, ip, response.answers[0].ttl)
                return ip
            elif is_noerror(response.header.flags) and not response.answers and response.header.num_authorities == 0:
                return None
            elif nsIP := get_nameserver_ip(response):
                nameserver = nsIP
            elif ns_domain := get_nameserver(response):
                nameserver = resolve(ns_domain, TYPE_A)
            elif cname := get_cname(response):
                domain_name = cname
                nameserver = "192.36.148.17"
            else:
                return None

"""
res=resolve("twitter.com",TYPE_A)
print(res)
res=resolve("www.facebook.com",TYPE_A)
print(res)
res=resolve("google.com",TYPE_AAAA)
print(res)
res=resolve("anits.org",TYPE_A)
print(res)
"""

