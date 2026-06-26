import ipaddress
RCODE_NOERROR  = 0
RCODE_FORMERR  = 1
RCODE_SERVFAIL = 2
RCODE_NXDOMAIN = 3
RCODE_NOTIMP   = 4
RCODE_REFUSED  = 5

def get_rcode(flags):
    return flags & 0xF

def is_nxdomain(flags):
    return get_rcode(flags) == RCODE_NXDOMAIN

def is_noerror(flags):
    return get_rcode(flags) == RCODE_NOERROR

def ip_to_string(ip):
    return ".".join([str(x) for x in ip])

def ip_to_string_v6(ip):
    return str(ipaddress.IPv6Address(ip))