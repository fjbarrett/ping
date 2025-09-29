from scapy.all import IP, TCP, sr1


def tcp_ping(host: str, port: int = 80, timeout: float = 5.0) -> dict:
    """
    Performs a TCP SYN ping to a specified host and port.
    """
    # Construct the TCP SYN packet
    pkt = IP(dst=host) / TCP(dport=port, flags="S")

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

        # Check for SYN-ACK or RST flags
        if response.haslayer(TCP):
            flags = response.getlayer(TCP).flags
            # A SYN-ACK (18) or RST (4) indicates a host is up.
            if flags == 0x12 or flags == 0x04:
                result["alive"] = True
                result["error"] = None
            else:
                result["error"] = "Unexpected TCP flags"
        elif response.haslayer(IP) and response.getlayer(IP).proto == 1:
            # Check for ICMP error, e.g., Port Unreachable
            result["error"] = "Received ICMP error"

    return result

    # Example usage
    # print(tcp_ping("8.8.8.8", port=53))
