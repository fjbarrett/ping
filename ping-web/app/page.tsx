"use client";

import Image from "next/image";
import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");

  async function callAPI(endpoint: string) {
    try {
      const res = await fetch(`http://127.0.0.1:8080/api/${endpoint}`);
      const data = await res.json();
      setMessage(JSON.stringify(data));
    } catch (err) {
      console.error(err);
      setMessage("Error calling API");
    }
  }

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <button
          onClick={() => callAPI("ping/icmp?host=8.8.8.8")}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Trigger Ping
        </button>

        <button
          onClick={() => callAPI("status")}
          className="px-4 py-2 bg-green-500 text-white rounded"
        >
          Check Status
        </button>

        {message && (
          <div className="mt-4 p-2 border rounded bg-gray-800">
            <pre>{message}</pre>
          </div>
        )}
      </main>
    </div>
  );
}
