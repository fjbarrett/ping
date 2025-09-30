"use client";

import { useState } from "react";

type Protocol = "icmp" | "tcp";

export default function Home() {
  const [message, setMessage] = useState("");
  const [host, setHost] = useState("");
  const [protocol, setProtocol] = useState<Protocol>("icmp");
  const [port, setPort] = useState<number | "">("");

  async function callAPI(endpoint: string) {
    try {
      const res = await fetch(`http://127.0.0.1:8080/api/${endpoint}`);
      const data = await res.json();
      setMessage(JSON.stringify(data, null, 2));
    } catch (err) {
      console.error(err);
      setMessage("Error calling API");
    }
  }

  function buildEndpoint() {
    if (!host) return "";
    if (protocol === "icmp") {
      return `ping/icmp?host=${encodeURIComponent(host.trim())}`;
    }
    // tcp
    const p = typeof port === "number" ? port : parseInt(String(port), 10);
    if (!Number.isFinite(p) || p < 1 || p > 65535) return "";
    return `ping/tcp?host=${encodeURIComponent(host.trim())}&port=${p}`;
  }

  const endpoint = buildEndpoint();
  const canPing =
    !!host.trim() && (protocol === "icmp" || (protocol === "tcp" && endpoint));

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 bg-gray-100 text-gray-900">
      <main className="flex flex-col gap-6 row-start-2 items-center sm:items-start w-full max-w-xl">
        {/* Host */}
        <label className="w-full">
          <span className="block mb-1 text-sm font-medium">Host</span>
          <input
            type="text"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="e.g. 8.8.8.8 or example.com"
            className="w-full px-3 py-2 border rounded bg-white text-gray-900"
          />
        </label>

        {/* Protocol + Port */}
        <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label>
            <span className="block mb-1 text-sm font-medium">Protocol</span>
            <select
              value={protocol}
              onChange={(e) => setProtocol(e.target.value as Protocol)}
              className="w-full px-3 py-2 border rounded bg-white text-gray-900"
            >
              <option value="icmp">ICMP (ping)</option>
              <option value="tcp">TCP (connect)</option>
            </select>
          </label>

          <label className={`${protocol === "tcp" ? "" : "opacity-60"}`}>
            <span className="block mb-1 text-sm font-medium">Port (TCP)</span>
            <input
              type="number"
              min={1}
              max={65535}
              value={port}
              onChange={(e) =>
                setPort(e.target.value === "" ? "" : Number(e.target.value))
              }
              placeholder="e.g. 80"
              disabled={protocol !== "tcp"}
              className="w-full px-3 py-2 border rounded bg-white text-gray-900 disabled:bg-gray-100"
            />
          </label>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={() => endpoint && callAPI(endpoint)}
            disabled={!canPing}
            className="px-4 py-2 border border-blue-400 text-blue-600 bg-blue-50 rounded hover:bg-blue-100 disabled:bg-gray-200 disabled:text-gray-400"
          >
            Trigger Ping
          </button>

          <button
            onClick={() => callAPI("status")}
            className="px-4 py-2 border border-green-400 text-green-600 bg-green-50 rounded hover:bg-green-100"
          >
            Check Status
          </button>
        </div>

        {/* Output */}
        {message && (
          <div className="w-full mt-2 p-3 border rounded bg-white text-gray-900 shadow">
            <pre className="whitespace-pre-wrap break-words">{message}</pre>
          </div>
        )}
      </main>
    </div>
  );
}
