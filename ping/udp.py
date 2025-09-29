from scapy.all import IP, UDP, ICMP, sr1


def udp_ping(host: str, port: int = 53000, timeout: float = 1.0) -> dict:
    """
    Performs a UDP ping by sending to a high, likely closed port.
    """
    # Construct the UDP packet
    pkt = IP(dst=host) / UDP(dport=port)

    # Send the packet and wait for a single response
    response = sr1(pkt, timeout=timeout, verbose=0)

    result = {
        "host": host,
        "port": port,
        "alive": False,
        "rtt_ms": None,
        "error": "No response",
    }

    if response:
        result["rtt_ms"] = round((response.time - pkt.sent_time) * 1000, 3)
        # Check for ICMP 'Port Unreachable' (type 3, code 3)
        if (
            response.haslayer(ICMP)
            and response.getlayer(ICMP).type == 3
            and response.getlayer(ICMP).code == 3
        ):
            result["alive"] = True
            result["error"] = None
        else:
            result["error"] = "Unexpected response or ICMP error"

    return result


# Example usage
# print(udp_ping("8.8.8.8"))
