from __future__ import annotations
import os, time, socket, random, statistics
from typing import Any, Dict, List, Optional, Tuple

from scapy.all import conf, sr1, send, IP, ICMP, Raw, IPv6, ICMPv6EchoRequest


def _resolve(host: str) -> Tuple[str, int]:
    """
    Return (ip, family). family = socket.AF_INET or socket.AF_INET6
    Prefer IPv4 unless host is explicitly IPv6 or only AAAA exists.
    """
    try:
        infos = socket.getaddrinfo(host, None, 0, 0, 0, socket.AI_ADDRCONFIG)
        # Prefer IPv4
        for fam in (socket.AF_INET, socket.AF_INET6):
            for af, _stype, _proto, _canon, sa in infos:
                if af == fam:
                    return sa[0], fam
    except Exception:
        pass
    # If it's a literal IP, detect family
    if ":" in host:
        return host, socket.AF_INET6
    return host, socket.AF_INET


# Construct ICMP or ICMPv6 packet
def _icmp_packet(
    ip: str, family: int, ident: int, seq: int, ttl: int, df: bool, payload: bytes
):
    if family == socket.AF_INET6 or ":" in ip:
        layer3 = IPv6(dst=ip, hlim=ttl)
        l4 = ICMPv6EchoRequest(id=ident, seq=seq)
    else:
        flags = "DF" if df else 0
        layer3 = IP(dst=ip, ttl=ttl, flags=flags)
        l4 = ICMP(id=ident, seq=seq)
    # Create packet using stacking
    pkt = layer3 / l4 / Raw(payload if payload else b"")
    return pkt


def ping_once(
    host: str,
    timeout: float = 1.0,
    iface: Optional[str] = None,
    ttl: int = 64,
    df: bool = False,
    payload: bytes = b"hello",
) -> Dict[str, Any]:
    # Send one echo request and return a result dict.
    ip, fam = _resolve(host)
    ident = (os.getpid() & 0xFFFF) ^ random.randint(0, 0xFFFF)
    seq = random.randint(0, 0xFFFF)
    pkt = _icmp_packet(ip, fam, ident, seq, ttl, df, payload)

    t0 = time.perf_counter()
    ans = sr1(pkt, timeout=timeout, verbose=0, iface=iface)
    t1 = time.perf_counter()

    rtt_ms = round((t1 - t0) * 1000.0, 3)

    result: Dict[str, Any] = {
        "host": host,
        "resolved_ip": ip,
        "alive": False,
        "packets_sent": 1,
        "packets_received": 0,
        "packet_loss_percent": 100.0,
        "min_response_time": None,
        "avg_response_time": None,
        "max_response_time": None,
        "rtt_ms": None,
        "icmp_type": None,
        "error": None,
        "raw": "",
    }

    if ans is None:
        # Could be filtered, timed out, or rate-limited
        result["error"] = "timeout/no reply"
        return result

    # Determine reply type
    try:
        if fam == socket.AF_INET6 or ":" in ip:
            if ans.haslayer(
                ICMPv6EchoRequest
            ):  # ICMPv6 echo *reply* is same class with type 129 internally handled
                pass
            # If the first upper layer is IPv6 with ICMPv6EchoRequest type 129, sr1 already matched it.
            # For diagnostics, record highest ICMPv6 layer present.
            icmp6 = ans.getlayer(ICMPv6EchoRequest)
            result["icmp_type"] = getattr(icmp6, "type", None)
        else:
            if ans.haslayer(ICMP):
                ict = ans.getlayer(ICMP).type
                result["icmp_type"] = ict
        # If we got any ICMP response back, count it
        result["packets_received"] = 1
        result["packet_loss_percent"] = 0.0
        result["alive"] = (
            True if result["icmp_type"] in (0, None) else True
        )  # treat time-exceeded/unreach as “got something”
        result["rtt_ms"] = rtt_ms
        result["min_response_time"] = rtt_ms
        result["avg_response_time"] = rtt_ms
        result["max_response_time"] = rtt_ms
        result["raw"] = repr(ans)
    except Exception as e:
        result["error"] = f"parse error: {e}"

    return result


def ping_icmp(
    host: str,
    count: int = 4,
    timeout: float = 1.0,
    interval: float = 0.2,
    iface: Optional[str] = None,
    ttl: int = 64,
    df: bool = False,
    payload: bytes = b"hello",
) -> Dict[str, Any]:
    """
    Multi-echo with stats, Scapy-based.
    """
    rtts: List[float] = []
    resolved_ip, _fam = _resolve(host)
    received = 0
    errors: List[str] = []

    for seq in range(count):
        res = ping_once(
            host, timeout=timeout, iface=iface, ttl=ttl, df=df, payload=payload
        )
        if res["packets_received"]:
            received += 1
            if res["rtt_ms"] is not None:
                rtts.append(res["rtt_ms"])
        if res.get("error"):
            errors.append(res["error"])
        if seq != count - 1:
            time.sleep(interval)

    loss = round(100.0 * (count - received) / max(count, 1), 2)
    out: Dict[str, Any] = {
        "host": host,
        "resolved_ip": resolved_ip,
        "alive": received > 0,
        "packets_sent": count,
        "packets_received": received,
        "packet_loss_percent": loss,
        "min_response_time": min(rtts) if rtts else None,
        "avg_response_time": round(statistics.fmean(rtts), 3) if rtts else None,
        "max_response_time": max(rtts) if rtts else None,
        "errors": errors,
    }
    return out


def ping_many_icmp(
    hosts: List[str],
    count: int = 2,
    timeout: float = 1.0,
    interval: float = 0.0,
    iface: Optional[str] = None,
    ttl: int = 64,
    df: bool = False,
    payload: bytes = b"hello",
) -> Dict[str, Any]:
    results = []
    alive = 0
    for h in hosts:
        r = ping_icmp(
            h,
            count=count,
            timeout=timeout,
            interval=interval,
            iface=iface,
            ttl=ttl,
            df=df,
            payload=payload,
        )
        results.append(r)
        if r["alive"]:
            alive += 1
    total = len(hosts)
    return {
        "results": results,
        "summary": {
            "alive_count": alive,
            "total_count": total,
            "success_rate": round((alive / total * 100.0), 2) if total else 0.0,
        },
    }
