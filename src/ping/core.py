from __future__ import annotations
import subprocess
import platform
import socket
import logging
from typing import Union, List, Dict, Any

logger = logging.getLogger("ping")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def _resolve_ipv4(host: str) -> List[str]:
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        return sorted({info[4][0] for info in infos})
    except Exception:
        return []

def ping_host(host: str, count: int = 10, timeout: int = 5) -> Dict[str, Any]:
    resolved_ips = _resolve_ipv4(host)
    resolved_ip = resolved_ips[0] if resolved_ips else None

    result: Dict[str, Any] = {
        "host": host,
        "alive": False,
        "packets_sent": count,
        "packets_received": 0,
        "packet_loss_percent": 100.0,
        "min_response_time": None,
        "avg_response_time": None,
        "max_response_time": None,
        "resolved_ip": resolved_ip,
        "error": None,
        "raw": "",
    }

    try:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

        logger.debug("Running ping command: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=(timeout * count + 10)
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        result["raw"] = out.strip()

        _parse_ping_output(out, result, system)

        if proc.returncode == 0:
            result["alive"] = True
        else:
            result["error"] = f"ping returned code {proc.returncode}"

    except subprocess.TimeoutExpired:
        result["error"] = f"Ping command timed out after {timeout * count + 10} seconds"
    except FileNotFoundError:
        result["error"] = "Ping command not found - ensure ping is installed and in PATH"
    except Exception as e:
        result["error"] = f"Ping failed: {e}"
        logger.debug("ping_host exception", exc_info=True)

    return result

def ping_hosts(
    hosts: List[str], count: int = 10, timeout: int = 5, print_live: bool = True
) -> Dict[str, Any]:
    if not hosts:
        return {
            "results": [],
            "summary": {"alive_count": 0, "total_count": 0, "success_rate": 0.0},
        }

    results = []
    alive_count = 0
    total = len(hosts)

    logger.info(
        "Starting ping scan of %d hosts (count=%d, timeout=%ds)", total, count, timeout
    )
    for idx, host in enumerate(hosts, start=1):
        logger.info("[%d/%d] Pinging %s...", idx, total, host)
        res = ping_host(host, count=count, timeout=timeout)
        results.append(res)

        if res["alive"]:
            alive_count += 1
            logger.info(
                "✔ %s is alive (avg=%s ms, loss=%s%%)",
                host, res["avg_response_time"], res["packet_loss_percent"]
            )
            if print_live:
                ip = res.get("resolved_ip") or host
                print(f"{host}\t{ip}")
        else:
            err = f" ({res['error']})" if res.get("error") else ""
            logger.info("✘ %s unreachable%s", host, err)

    success_rate = (alive_count / total * 100.0) if total else 0.0
    logger.info("Ping scan complete: %d/%d alive (%.2f%%).", alive_count, total, success_rate)

    return {
        "results": results,
        "summary": {
            "alive_count": alive_count,
            "total_count": total,
            "success_rate": round(success_rate, 2),
        },
    }

def scan_ping(
    target: Union[str, List[str]],
    count: int = 10,
    timeout: int = 5,
    print_live: bool = False,
) -> Dict[str, Any]:
    if isinstance(target, str):
        return ping_host(target, count=count, timeout=timeout)
    elif isinstance(target, list):
        return ping_hosts(target, count=count, timeout=timeout, print_live=print_live)
    else:
        return {"error": "target must be a string or list of strings"}

def _parse_ping_output(output: str, result: Dict[str, Any], system: str) -> None:
    try:
        lines = (output or "").lower().splitlines()
        if system == "windows":
            for line in lines:
                if "packets:" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "received =" in part:
                            try:
                                result["packets_received"] = int(part.split("=")[1].strip())
                            except Exception:
                                pass
                        elif "loss)" in part and "%" in part:
                            try:
                                loss_str = part.split("(")[1].split("%")[0].strip()
                                result["packet_loss_percent"] = float(loss_str)
                            except Exception:
                                pass
                elif "average =" in line:
                    try:
                        avg = line.split("average =")[1].split("ms")[0].strip()
                        result["avg_response_time"] = float(avg)
                    except Exception:
                        pass
        else:
            for line in lines:
                if "packets transmitted" in line:
                    parts = [p.strip() for p in line.split(",")]
                    for part in parts:
                        if part.endswith("received"):
                            try:
                                result["packets_received"] = int(part.split()[0])
                            except Exception:
                                pass
                        if "packet loss" in part and "%" in part:
                            try:
                                num = "".join(ch for ch in part if ch.isdigit() or ch == ".")
                                result["packet_loss_percent"] = float(num) if num else 100.0
                            except Exception:
                                pass
                elif ("rtt" in line or "round-trip" in line) and "=" in line:
                    try:
                        stats = line.split("=")[1].strip().split("/")
                        if len(stats) >= 3:
                            result["min_response_time"] = float(stats[0])
                            result["avg_response_time"] = float(stats[1])
                            result["max_response_time"] = float(stats[2])
                    except Exception:
                        pass
    except Exception:
        logger.debug("Failed to parse ping output", exc_info=True)

def main_cli():
    import sys
    hosts = sys.argv[1:]
    if not hosts:
        print("Usage: ping-cli host [host2 ...]")
        raise SystemExit(2)
    res = ping_hosts(hosts, count=3, timeout=3, print_live=True)
    ok = res["summary"]["alive_count"] > 0
    raise SystemExit(0 if ok else 1)
