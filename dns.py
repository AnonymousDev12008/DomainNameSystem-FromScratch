import socket
from io import BytesIO

"""query=build_query("www.anits.org",1)

sockt=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sockt.sendto(query,("8.8.8.8",53))
response,_ = sockt.recvfrom(1024)"""



"""reader=BytesIO(response)
parse_header(reader)
parse_question(reader)
parse_record(reader)"""

def lookup_domain(domain_name):
    query = build_query(domain_name,TYPE_A)
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.sendto(query,("8.8.8.8",53))

    data,_=sock.recvfrom(1024)
    response=parse_DNSPacket(data)
    for record in response.answers:
        if record.type_ == TYPE_A:
            return ip_to_string(record.data)

#dns_client making queries and getting back from a resolver (8.8.8.8)
"""print(lookup_domain("anits.edu.in"))
print(lookup_domain("google.com"))
print(lookup_domain("purplegene.in"))
print(lookup_domain("www.facebook.com"))"""

#print((send_query("8.8.8.8","example.com",TYPE_NS)).answers)

#print((send_query("198.41.0.4","google.com",TYPE_A)).authorities)

#print((send_query("192.203.230.10","google.com",TYPE_A)).additionals)

#res=resolve_flawed("google.com",TYPE_A)
#print(res)





