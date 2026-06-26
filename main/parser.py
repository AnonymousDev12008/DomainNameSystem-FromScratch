
from models import DNSQuestion,DNSHeader,DNSRecord,DNSPacket
import struct
from io import BytesIO
from utils import ip_to_string,ip_to_string_v6

TYPE_A=1
TYPE_NS=2
CLASS_IN=1
TYPE_CNAME=5
TYPE_AAAA=28
TYPE_OPT=41

def parse_header(reader):
    items=struct.unpack("!HHHHHH",reader.read(12))
    return DNSHeader(*items)

def parse_name_v1(reader):
    parts=[]
    while (length := reader.read(1)[0]) != 0:
        parts.append(reader.read(length))
    return b".".join(parts)

def parse_question(reader):
    name=parse_name_v1(reader)
    data=reader.read(4)
    type_,class_=struct.unpack("!HH",data)
    return DNSQuestion(name,type_=type_,class_=class_)

def parse_name_v2(reader):
    parts = []
    while True:
        byte = reader.read(1)
        if not byte:
            break
        length = byte[0]
        if length == 0:
            break
        if length & 0b1100_0000:
            parts.append(parse_compressed_name(length, reader))
            break
        else:
            parts.append(reader.read(length))
    return b".".join(parts)

def parse_compressed_name(length,reader):
    pointer_bytes=bytes([length & 0b0011_1111]) + reader.read(1)
    pointer=struct.unpack("!H",pointer_bytes)[0]
    current_pos=reader.tell()
    reader.seek(pointer)
    result=parse_name_v2(reader)
    reader.seek(current_pos)
    return result

def parse_record(reader):
    name = parse_name_v2(reader)
    data_m = reader.read(10)
    if len(data_m) < 10:
        return None
    type_,class_,ttl,data_len = struct.unpack("!HHIH", data_m)
    if type_ == TYPE_OPT:
        reader.read(data_len)
        return None
    elif type_ == TYPE_NS:
        data = parse_name_v2(reader)
    elif type_ == TYPE_CNAME:
        data = parse_name_v2(reader)
    elif type_ == TYPE_A:
        data = ip_to_string(reader.read(data_len))
    elif type_ == TYPE_AAAA:
        data = ip_to_string_v6(reader.read(data_len))
    else:
        data = reader.read(data_len)
    return DNSRecord(name, type_, class_, ttl, data)

def parse_DNSPacket(data):
    reader = BytesIO(data)
    header = parse_header(reader)
    questions = [parse_question(reader) for _ in range(header.num_questions) ]
    answers = [parse_record(reader) for _ in range(header.num_answers)]
    authorities = [parse_record(reader) for _ in range(header.num_authorities)]
    additionals = [parse_record(reader) for _ in range(header.num_additionals)]

    return DNSPacket(header,questions,answers,authorities,additionals)



