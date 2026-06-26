

# DomainNameSystem-Broken Down and Rebuilt

tried building a network level DNS blocker. ended up writing a full iterative DNS resolver with a blocklist from scratch.

turns out DNS is just structured bytes over UDP. once you see that, everything makes sense.

---

## How it works

most resolvers forward your query to 8.8.8.8 and let Google do the work. this one does it itself.

when you query `google.com` it starts at a root server, gets referred to the `.com` TLD server, gets referred to Google's authoritative nameserver, and finally gets the IP. result gets cached with the TTL from the record so the next query is instant. if the domain is on the blocklist it never hits the network — returns NXDOMAIN immediately.

full technical walkthrough in `DOCUMENTATION.md`.

---

## How to use

**run the resolver:**
```bash
python main.py
```

**test with dig:**
```bash
dig @127.0.0.1 -p 8035 google.com
dig @127.0.0.1 -p 8035 cdn.jsdelivr.net    # watch the CNAME chain
dig @127.0.0.1 -p 8035 instagram.com       # blocked → NXDOMAIN
dig @127.0.0.1 -p 8035 amazon.in AAAA      # no record → NOERROR empty
```

**use as actual home DNS** — run as administrator on Windows:
on one caution only if you know what you are doing and are sure you can revoke things back
```bash
net stop "DNS Client"
# change port to 53 in main.py
# point network adapter DNS to 127.0.0.1
```

---

## Blocklist

create a `blocklist.txt` file in the project root. two formats supported:

**hosts file format** {most common, works with community lists like StevenBlack}:
```
0.0.0.0 instagram.com
0.0.0.0 www.instagram.com
0.0.0.0 doubleclick.net
0.0.0.0 ads.google.com
```

**plain domain format**:
```
instagram.com
facebook.com
doubleclick.net
```

lines starting with `#` are treated as comments and ignored:
```
# social media
0.0.0.0 instagram.com

# ads
0.0.0.0 doubleclick.net
```

no `blocklist.txt` — resolver runs without blocking, no crash.

community maintained lists in hosts format that drop straight in — StevenBlack unified hosts {~100k domains}, Pi-hole format lists work too.

---

## Troubleshooting

**first query times out, second is instant** — cold start. upstream servers aren't cached yet. normal behavior, cache warms up after first resolution.

**something went wrong exception** — domain exists but has no record of the requested type. try querying TYPE_A instead.

**port already in use on 8035** — something else is running on that port. change the port number in `main.py`.

**port 53 access denied** — needs admin on Windows. run IntelliJ or terminal as administrator.

**SQLite thread error** — make sure `check_same_thread=False` is set in `cache.py`.

---

## Structure

```
models.py    → DNS data structures
encoder.py   → build DNS queries
parser.py    → parse DNS responses
resolver.py  → iterative resolution logic
cache.py     → SQLite TTL cache
blocklist.py → domain blocking
network.py   → UDP socket handling
main.py      → listener + response builder
utils.py     → helpers
```

---

## what's next

TCP fallback for large responses, DNSSEC validation, DNS over TLS, point the home router at it so every device goes through this resolver.

---

## built on

RFC 1035, RFC 2308, Julia Evans — DNS in a Weekend

---

## feedback welcome

this is a learning project — if you see something wrong, something that could be better, or just want to talk DNS, open an issue or reach out on LinkedIn.

---

Built by P.Sai.Manikantha.Reddy