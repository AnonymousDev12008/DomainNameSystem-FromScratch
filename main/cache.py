import sqlite3
import time
import threading

lock = threading.Lock()
dnsCache = sqlite3.connect("dnsCache.db", check_same_thread = False)
cursr = dnsCache.cursor()

def cache_init():
    cursr.execute("""
                  CREATE TABLE IF NOT EXISTS dns_cache (
                                                       domain      TEXT,
                                                       record_type INTEGER,
                                                       data        TEXT,
                                                       expires_at  REAL,
                                                       PRIMARY KEY (domain, record_type)
                  )
              """)
    dnsCache.execute("PRAGMA journal_mode=WAL")
    dnsCache.commit()

def cache_set(domain, record_type, data, ttl):
    expires_at = time.time()+ttl
    with lock:
        cursr.execute("""
            INSERT OR REPLACE INTO dns_cache
            (domain, record_type, data, expires_at)
            VALUES
            (?, ?, ?, ?)
        """,(domain,record_type,data,expires_at))
        dnsCache.commit()

def cache_get(domain, record_type):
    cursr.execute("""
    
        SELECT data, expires_at 
        FROM dns_cache
        WHERE domain = ? AND record_type = ?
    
    """,(domain, record_type))
    row=cursr.fetchone()
    if row is None:
        return None
    data, expires_at = row
    if time.time() > expires_at:
        cursr.execute("""
            DELETE FROM dns_cache
            WHERE  domain = ? AND record_type = ?
                
        """,(domain, record_type))
        dnsCache.commit()
        return None
    return data
