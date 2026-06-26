blocklist = set()

def load_blocklist(filepath):
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) == 2:
                    blocklist.add(parts[1])  # hosts format: 0.0.0.0 domain
                elif len(parts) == 1:
                    blocklist.add(parts[0])  # plain domain format
        print(f"blocklist loaded — {len(blocklist)} domains blocked")
    except FileNotFoundError:
        print("no blocklist.txt found, running without blocklist")

def is_blocked(domain):
    return domain.rstrip(".") in blocklist

def add_domain(domain):
    blocklist.add(domain.rstrip("."))

def remove_domain(domain):
    blocklist.discard(domain.rstrip("."))