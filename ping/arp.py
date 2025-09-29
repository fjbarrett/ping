from scapy.all import Ether, ARP, srp


def arp_ping(host_ip: str, timeout: float = 1.0) -> dict:
    """
    Performs an ARP ping on the local network segment.
    """
    # Create an ARP request for the target IP, broadcasting on Layer 2
    arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=host_ip)

    # Send the packet and wait for a response
    answered, unanswered = srp(arp_request, timeout=timeout, verbose=0)

    result = {"host": host_ip, "alive": False, "rtt_ms": None, "error": "No response"}

    if answered:
        # srp returns a list of (sent packet, received packet) tuples
        sent_pkt, received_pkt = answered[0]
        result["rtt_ms"] = round((received_pkt.time - sent_pkt.time) * 1000, 3)
        result["alive"] = True
        result["error"] = None

    return result


# Example usage (must be on the same local network as the target)
# print(arp_ping("google.com"))
