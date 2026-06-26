# DomainNameSystem Documentation :

## Structure :

### models.py :

models.py consists of all the dataclasses including
1. DNSHeader - 6 fields and each of 2 bytes {id,flag,num_questions,num_answers,num_authorities,num_additionals}.
2. DNSQuestion - 3 fields { name , _type , _class }.
3. DNSRecord - More like a resource record consisting of about 6 fields along with the absent rdatalen {name,type_,class_,ttl,rdata}
4. DNSPacket - More like an integrated DNSPacket with a header i.e. is always single but when comes to questions ,it is a list of DNSQuestion's and answers is a List[DNSRecord] the same with the case of authorities and additionals.

### encoders.py :

encoder.py consists of functions that help us encode the question and header into wire format {_to_bytes functions}
it includes :

1. header_to_bytes(header):

   functioning to help us convert all dataclass fields in as tuple and then encode it using struct pack and format it using "!HHHHHH"
   !-maintain network_byte order {big endian}
   H-unsigned 2 byte int
   6 fields to encode and thus 6 H's go in there
   return the packed byte form of question packed together with about a size of 12 bytes.

2. name_to_bytes(domain_name):

   converts the domain_name into RFC 1035 preferred byte/wire format
   split the domain name (encoded) for a b"." and then prepend the length before each split label and at last append a zero{root}.
   return the concatenated domain_name bytes object.

3. question_to_bytes(DNSQuestion):

   converts the DNSQuestion into a packed bytes object of type_ and class_ concatenated with encoded domain_name bytes object in total returning a packed DNSQuestion Bytes object.

4. build_query(domain_name,record_type):

   builds an in total packed dnsquery with question and header along with a truly random random.randint(0,65535) id for the dnsQuery, seed removed to avoid predictable IDs and cache poisoning risk. flags=0 since we are now an iterative resolver doing the work ourselves, no recursion desired. finally create DNSHeader and DNSQuestion and return a concatenated DNSQuery(DNSHeader+DNSQuestion{both encoded}).

5. record_to_bytes(DNSRecord):

   reverse of parse_record — converts a DNSRecord back to wire format for building responses. name is always \xc0\x0c {compression pointer to offset 12} since answer names always point back to the question name in the response. TYPE_A data converted from ip string back to 4 raw bytes via socket.inet_aton, TYPE_AAAA via socket.inet_pton with AF_INET6 for 16 bytes, TYPE_NS and TYPE_CNAME rdata re-encoded as domain name via encode_dns_name. isinstance checks handle both str and bytes coming in from DNSRecord data field since parse paths are inconsistent. returns concatenated name + struct.pack("!HHIH") fixed 10 byte header + rdata.


### parser.py :

parser contains functions that help in parsing the response for a query and this is also distributed along parsing the data , header , question and domain_name back along with implications of truncation{yet to be implemented} and compression {implemented in V2}

1. parse_header(reader:BytesIO):

   unpack the packed struct in the similar format with data coming in from the reader object upon reading 12 bytes since 6 fields and each of value 2 bytes implies the reader to read about 12 bytes and then unpack those values and return a DNSHeader object with those parameters.

2. parse_name_v1(reader:BytesIO):

   same logic using a walrus operator to first check if the length prepended of the following label is not zero in order to check if we hit an end and along the walrus catching the length ,and we thus add them to parts and then join parts together ,and we are good to go with the name back into normal form but here arisen the issue of DNSCompression domain_names sometimes are compressed by a pointer pointing to their first occurrence and this could actually happen to reduce size, and then we have to go back there for that domain_name.

3. parse_question(reader):

   parse the name using the parse_name_v1 and then unpack the type and class back and return a DNSQuestion object with these parameters.

4. parse_name_v2(reader):

   parses as usual but upon encountering a length with bits 11 we get to know compression has been implemented for the label, and we transfer the control over to the parse_compressed_name now that inside the parse_compressed_name we get to have the pointer bytes which is obtained by stripping top 2 bits of byte 1 + the next byte gives the offset to get the label this is done by seek and calling parse_name_v2 from there in a recursive functioning between parse_name_v2 and compressed_name_parse and also now we bring the pointer back to normal position and go. also now guarded against empty reads — if reader.read(1) returns b"" we break out safely instead of crashing on b""[0]{OPT RECORDS}.

5. parse_record(reader):

   does the record parsing by first parsing the name then type, class, TTL, rdatalen, rdata. handles TYPE_A {1} by converting 4 bytes to ip string, TYPE_NS {2} and TYPE_CNAME {5} by parsing the rdata as a domain name through parse_name_v2, TYPE_AAAA {28} by converting 16 bytes to ipv6 string via ipaddress.IPv6Address. special case — TYPE_OPT {41} is an EDNS0 metadata record carrying things like max UDP payload size, not a real DNS record, so we skip its data and return None. parse_DNSPacket filters these None returns out so they never pollute answers/authorities/additionals. added a guard on data_m length too incase reader runs out mid record.

6. parse_DNSPacket(data):

   does the parsing for the header and questions and answers and authorities and additionals and return the DNSPacket with all parsed data. now filters None from parse_record to handle OPT records cleanly.

### network.py :

does all the socket work forwarding the requests and receiving back from them, build a query and socket receiving data with a buffer size 1024(512*2). implements socket.settimeout(5) to avoid hanging between iterative chains and retries up to 3 times before giving up, a single packet drop shouldn't kill the whole resolution chain. TCP fallback yet to be implemented for truncated responses.

1. send_query(ip_address, domain_name, record_type):

   handles the socket work sending to port 53 and receiving with a buffer size 1024(512*2). retries 3 attempts on timeout printing attempt count before raising exception on all retries failing. returns a parsed DNSPacket back.

### utils.py :

utility functions and DNS response code constants.

1. ip_to_string(ip):

   converts the byte format IPv4 ip into a str using list comprehensions and join ".". returning an ip in string format.

2. ip_to_string_v6(ip):

   converts 16 raw bytes into a proper IPv6 string using ipaddress.IPv6Address — handles the :: compression formatting automatically. no point doing that manually.

3. get_rcode(flags):

   extracts the bottom 4 bits of the DNS header flags field — these are the RCODE bits telling us the response status. RCODE values defined as constants {RCODE_NOERROR=0, RCODE_FORMERR=1, RCODE_SERVFAIL=2, RCODE_NXDOMAIN=3, RCODE_NOTIMP=4, RCODE_REFUSED=5}.

4. is_nxdomain(flags):

   returns True if rcode == RCODE_NXDOMAIN {3} — domain flat out doesn't exist.

5. is_noerror(flags):

   returns True if rcode == RCODE_NOERROR {0} — query succeeded even if answer section is empty.

### cache.py :

SQLite backed persistent DNS cache. survives process restarts unlike a plain dictionary. WAL mode enabled for concurrent access when multiple devices hit the resolver simultaneously.

schema — dns_cache table with {domain, record_type, data, expires_at} and a composite PRIMARY KEY on (domain, record_type) so same domain can have separate A and AAAA entries. expires_at stored as REAL {unix timestamp float} from time.time() + ttl.

1. cache_init():

   CREATE TABLE IF NOT EXISTS — safe to call every startup, never wipes existing data. also sets PRAGMA journal_mode=WAL for concurrent read safety across devices.

2. cache_set(domain, record_type, data, ttl):

   INSERT OR REPLACE — overwrites stale entry if same primary key exists. expires_at = time.time() + ttl. commits to disk immediately.

3. cache_get(domain, record_type):

   SELECT by (domain, record_type), fetchone(). if None — cache miss, return None. if found but time.time() > expires_at — expired, DELETE and return None so resolver fetches fresh. if fresh — return data directly. zero network hops on cache hit.

threading — sqlite connection created with check_same_thread=False to allow access from multiple threads since each query runs in its own thread. write operations wrapped in threading.Lock() to prevent concurrent writes corrupting the database. reads left unlock less since WAL mode handles concurrent reads natively without contention. lock only on cache_set — cache_get reads are safe without it.

### resolver.py :

handles the resolving functions and internal utilities.

1. get_answer(packet, record_type):

   checks answers section for matching record_type and returns data — now record_type aware so AAAA queries look for AAAA records not just A.

2. get_cname(packet):

   checks for CNAME records in answers incase have to resolve through cname and returns the cname decoded to resolve.

3. get_nameserver_ip(packet):

   checks TYPE_A in additionals for the nameserver glue IP {fast path on referral} — skips having to resolve the nameserver name separately.

4. get_nameserver(packet):

   if additionals absent we fall back to authorities for the NS domain name — slower path, requires recursive resolve of NS name before continuing.

5. resolve(domain_name, record_type):

   checks cache first before any network call — cache hit returns immediately. on miss sets up root nameserver and enters while True iterative loop. checks RCODE on every response — NXDOMAIN gets cached for NXDOMAIN_TTL {300s} and returned immediately, no point querying further for a nonexistent domain. on answer — cache_set with TTL from record and return. on glue IP — update nameserver directly. on NS domain — recursively resolve NS name to get its IP. on CNAME — update domain_name and reset to root. on NOERROR with empty answers and no authorities — domain exists but no record of this type, return None cleanly. retry logic in send_query handles transient timeouts before this loop sees a failure.

   negative caching — NXDOMAIN responses cached so repeated queries for nonexistent domains never hit the network. distinct from NOERROR+empty which is not cached since record types can be added to a domain later.{RFC 2308}

### blocklist.py :

a set based domain blocklist loaded at startup. O(1) lookup per query — set not list so it never slows down regardless of how many domains are blocked. supports both hosts file format {0.0.0.0 domain} and plain domain format {one domain per line}. ignores comments and empty lines.

1. load_blocklist(filepath):

   opens the blocklist file and parses line by line. strips comments {#} and empty lines. splits each line — if two parts takes the second {hosts format}, if one part takes it directly {plain format}. adds to the blocklist set. prints count of blocked domains on load. gracefully handles missing file — resolver runs without blocklist rather than crashing.

2. is_blocked(domain):

   checks if domain exists in blocklist set after stripping trailing dot — DNS sometimes appends a trailing dot {instagram.com.} and we need both forms to match. returns True if blocked.

3. add_domain(domain):

   adds a domain to the in-memory blocklist at runtime. does not persist to file — restart loses it. useful for dynamic blocking without restarting the resolver.

4. remove_domain(domain):

   removes a domain from the in-memory blocklist using discard — unlike remove, discard doesn't throw if domain isn't present.


### main.py :

entry point and UDP listener. binds to port 8035 for testing {port 53 needs admin and disabling Windows DNS client service}. each incoming query spawns a thread so slow resolutions don't block other clients. shared socket passed to threads — UDP socket is thread safe for sendto.

1. build_response(query_packet, ip):

   builds a valid DNS response packet for a successful resolution. copies ID from incoming query so client matches response to request. flags=0x8180 {QR=1 response, RD=1 recursion desired, RA=1 recursion available, RCODE=0 noerror}. answer name is \xc0\x0c — compression pointer back to offset 12 where question name lives, standard practice. question section re-encoded from parsed name back to wire format via encode_dns_name. returns concatenated header + question + answer record bytes.

2. build_error_response(query_packet, error_type):

   builds a DNS error response with no answer section. NXDOMAIN sets flags=0x8183 {RCODE=3}, SERVFAIL sets flags=0x8182 {RCODE=2}, NOERROR empty sets flags=0x8180 {RCODE=0}. used for blocked domains, nonexistent domains, resolver failures, and record types with no data.

3. handle_query(data, addr, sock):

   per-thread query handler. parses incoming raw bytes into DNSPacket, extracts domain and record_type from question section. checks blocklist first — blocked domains return NXDOMAIN immediately without hitting the network. calls resolve() and builds appropriate response based on result — ip string gets build_response, None gets NOERROR empty, NXDOMAIN string gets NXDOMAIN error response. exceptions caught and returned as SERVFAIL so client gets a response instead of timing out.

4. start_listener():

   binds UDP socket to 0.0.0.0:8035 and loops forever on recvfrom. each incoming query spawns a daemon thread running handle_query — daemon=True means threads die with the main process, no zombie threads. listener never blocks on resolution, concurrent queries resolve in parallel.

