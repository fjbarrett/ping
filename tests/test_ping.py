# tests/test_ping.py
import types

from ping import core as ping  # <-- change this line


def make_proc(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Minimal object that quacks like CompletedProcess for our use."""
    p = types.SimpleNamespace()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


def test_ping_host_parses_unix_success(monkeypatch):
    # Fake we're on Linux/macOS
    monkeypatch.setattr(ping.platform, "system", lambda: "Linux")

    # Provide a deterministic DNS resolution
    monkeypatch.setattr(
        ping.socket,
        "getaddrinfo",
        lambda host, *_args, **_kwargs: [
            (None, None, None, None, ("93.184.216.34", 0))
        ],
    )

    # Typical Unix ping output
    unix_out = (
        "PING example.com (93.184.216.34): 56 data bytes\n"
        "--- example.com ping statistics ---\n"
        "5 packets transmitted, 5 received, 0% packet loss, time 4004ms\n"
        "rtt min/avg/max/mdev = 10.123/20.456/30.789/0.123 ms\n"
    )
    monkeypatch.setattr(
        ping.subprocess, "run", lambda *a, **k: make_proc(stdout=unix_out, returncode=0)
    )

    res = ping.ping_host_cmd("example.com", count=5, timeout=1)
    assert res["alive"] is True
    assert res["packets_sent"] == 5
    assert res["packets_received"] == 5
    assert res["packet_loss_percent"] == 0.0
    assert res["avg_response_time"] == 20.456
    assert res["resolved_ip"] == "93.184.216.34"


def test_ping_host_parses_windows_success(monkeypatch):
    # Fake Windows
    monkeypatch.setattr(ping.platform, "system", lambda: "Windows")

    # Skip real DNS
    monkeypatch.setattr(
        ping.socket,
        "getaddrinfo",
        lambda *a, **k: [(None, None, None, None, ("1.2.3.4", 0))],
    )

    win_out = (
        "Pinging example.com [1.2.3.4] with 32 bytes of data:\n"
        "Reply from 1.2.3.4: bytes=32 time=10ms TTL=58\n"
        "\n"
        "Ping statistics for 1.2.3.4:\n"
        "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
        "Approximate round trip times in milli-seconds:\n"
        "    Minimum = 8ms, Maximum = 12ms, Average = 10ms\n"
    )
    monkeypatch.setattr(
        ping.subprocess, "run", lambda *a, **k: make_proc(stdout=win_out, returncode=0)
    )

    res = ping.ping_host_cmd("example.com", count=4, timeout=1)
    assert res["alive"] is True
    assert res["packets_received"] == 4
    assert res["packet_loss_percent"] == 0.0
    assert res["avg_response_time"] == 10.0


def test_ping_host_handles_nonzero_exit(monkeypatch):
    monkeypatch.setattr(ping.platform, "system", lambda: "Linux")
    monkeypatch.setattr(ping.socket, "getaddrinfo", lambda *a, **k: [])
    # Non-zero exit code from ping
    monkeypatch.setattr(
        ping.subprocess,
        "run",
        lambda *a, **k: make_proc(stdout="no reply", returncode=1),
    )

    res = ping.ping_host_cmd("bad.example", count=1, timeout=1)
    assert res["alive"] is False
    assert res["error"] and "return" in res["error"].lower()


def test_ping_hosts_aggregates(monkeypatch, capsys):
    # Monkeypatch ping_host to avoid subprocess entirely
    def fake_ping_host(host, **_):
        return {
            "host": host,
            "alive": (host != "down.example"),
            "packets_sent": 3,
            "packets_received": 3 if host != "down.example" else 0,
            "packet_loss_percent": 0.0 if host != "down.example" else 100.0,
            "min_response_time": 5.0 if host != "down.example" else None,
            "avg_response_time": 10.0 if host != "down.example" else None,
            "max_response_time": 15.0 if host != "down.example" else None,
            "resolved_ip": "203.0.113.5" if host != "down.example" else None,
            "error": None if host != "down.example" else "timeout",
            "raw": "",
        }

    monkeypatch.setattr(ping, "ping_host_cmd", fake_ping_host)

    res = ping.ping_hosts_cmd(
        ["ok.example", "down.example", "ok2.example"],
        count=3,
        timeout=1,
        print_live=True,
    )
    assert res["summary"]["alive_count"] == 2
    assert res["summary"]["total_count"] == 3
    assert res["summary"]["success_rate"] == round(2 / 3 * 100, 2)

    # print_live prints host\tip for alive hosts; verify something printed
    out = capsys.readouterr().out
    assert "ok.example" in out and "ok2.example" in out
