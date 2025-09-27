# tests/test_icmp.py
import types
import pytest
import socket

# Skip whole file if scapy isn't available
pytest.importorskip("scapy.all")

from ping import icmp as ping_icmp_mod  # your module with ping_icmp / ping_many_icmp


def _fake_dns(monkeypatch, ip="203.0.113.10"):
    monkeypatch.setattr(
        ping_icmp_mod.socket,
        "getaddrinfo",
        lambda host, *_a, **_k: [(socket.AF_INET, None, None, None, (ip, 0))],
    )


def _fake_sr1_reply(icmp_type=0):
    """Return an object that quacks like a Scapy packet for our needs."""

    class FakeICMP:
        def __init__(self, t):
            self.type = t

    class FakePkt:
        def __init__(self, t):
            self._t = t

        def haslayer(self, layer):
            return True

        def getlayer(self, layer):
            return FakeICMP(self._t)

        def __repr__(self):
            return "<FakePkt>"

    return FakePkt(icmp_type)


def test_ping_once_success(monkeypatch):
    _fake_dns(monkeypatch, ip="93.184.216.34")

    # Patch sr1 to return an immediate echo-reply
    monkeypatch.setattr(
        ping_icmp_mod, "sr1", lambda *a, **k: _fake_sr1_reply(icmp_type=0)
    )

    res = ping_icmp_mod.ping_once("example.com", timeout=0.1, payload=b"x" * 8)
    assert res["alive"] is True
    assert res["packets_received"] == 1
    assert res["packet_loss_percent"] == 0.0
    assert res["resolved_ip"] == "93.184.216.34"
    assert res["rtt_ms"] is not None


def test_ping_once_timeout(monkeypatch):
    _fake_dns(monkeypatch)
    # No reply
    monkeypatch.setattr(ping_icmp_mod, "sr1", lambda *a, **k: None)

    res = ping_icmp_mod.ping_once("no-reply.example", timeout=0.01)
    assert res["alive"] is False
    assert res["packets_received"] == 0
    assert res["error"]  # "timeout/no reply"


def test_ping_icmp_aggregates(monkeypatch):
    _fake_dns(monkeypatch)
    # Always reply
    monkeypatch.setattr(
        ping_icmp_mod, "sr1", lambda *a, **k: _fake_sr1_reply(icmp_type=0)
    )
    # Avoid real sleeps in tests
    monkeypatch.setattr(ping_icmp_mod.time, "sleep", lambda *_: None)

    res = ping_icmp_mod.ping_icmp("ok.example", count=3, timeout=0.05, interval=0.0)
    assert res["packets_sent"] == 3
    assert res["packets_received"] == 3
    assert res["packet_loss_percent"] == 0.0
    assert res["alive"] is True


def test_ping_many_icmp(monkeypatch):
    _fake_dns(monkeypatch)
    monkeypatch.setattr(ping_icmp_mod, "sr1", lambda *a, **k: _fake_sr1_reply(0))
    monkeypatch.setattr(ping_icmp_mod.time, "sleep", lambda *_: None)

    res = ping_icmp_mod.ping_many_icmp(
        ["a.example", "b.example"], count=2, timeout=0.05
    )
    assert res["summary"]["alive_count"] == 2
    assert res["summary"]["total_count"] == 2
