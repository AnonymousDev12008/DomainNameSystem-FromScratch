from dataclasses import dataclass
from typing import List

@dataclass
class DNSHeader:
    id : int
    flags : int
    num_questions: int=0
    num_answers: int=0
    num_authorities: int=0
    num_additionals: int=0

@dataclass
class DNSQuestion:
    name:bytes
    type_:int
    class_:int

@dataclass
class DNSRecord:
    name:bytes
    type_:int
    class_:int
    ttl:int
    data:bytes

@dataclass
class DNSPacket:
    header  : DNSHeader
    questions : List[DNSQuestion]
    answers : List[DNSRecord]
    authorities : List[DNSRecord]
    additionals : List[DNSRecord]

