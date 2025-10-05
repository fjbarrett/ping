import socket


def rdns_lookup(ip: str) -> dict:
    # Perform a reverse DNS lookup for the given IP address
    result = {
        "ip": ip,
        "domain": None,
        "error": None,
    }
    try:
        domain = socket.gethostbyaddr(ip)
        result["domain"] = domain[0]
    except socket.herror as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result
