"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState("loading");
  const [models, setModels] = useState<any[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadData() {
    try {
      const statusRes = await fetch("/api/ollama/status");
      const statusData = await statusRes.json();

      const nodesRes = await fetch("/api/nodes");
      const nodesData = await nodesRes.json();

      setStatus(statusData.status);
      setModels(statusData.models || []);
      setNodes(nodesData || []);
    } catch {
      setStatus("error");
    }
  }

  async function sendPrompt() {
    if (!prompt) return;

    setLoading(true);
    setResponse("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "tinyllama:latest",
          prompt: prompt,
        }),
      });

      const data = await res.json();
      setResponse(data.response);
    } catch {
      setResponse("Error talking to model.");
    }

    setLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <h1 className="text-4xl font-bold mb-8">ModelDock</h1>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl mb-10">
        <h2 className="text-2xl mb-4">Add Computer</h2>

        <p className="text-zinc-400 mb-4">
          Install ModelDock Agent on another comuter or GPU server.
        </p>
        
        <div className="relative">
          <button

            onClick={() => {
		alert("Copy this command:\n\ncurl -sSL https://raw.githubusercontent.com/kgil0/modeldock/main/scripts/install-agent.sh | bash");
              
            }}
            className="absolute top-3 right-3 bg-zinc-800 hover:bg-zinc-700 px-3 py-1 rounded text-sm"
          >
            Copy
          </button>

          <code className="block bg-zinc-900 p-4 rounded text-sm overflow-x-auto">
            curl -sSL https://raw.githubusercontent.com/kgil0/modeldock/main/scripts/install-agent.sh | bash
          </code>
        </div>
        
      </section>

      <div className="grid gap-6 md:grid-cols-2 mb-10">
        <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl">
          <h2 className="text-2xl mb-3">Ollama Status</h2>
          <div
            className={`inline-block px-4 py-2 rounded ${
              status === "connected" ? "bg-green-600" : "bg-red-600"
            }`}
          >
            {status}
          </div>
        </section>

        <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl">
          <h2 className="text-2xl mb-3">Installed Models</h2>
          <div className="space-y-2">
            {models.map((model: any) => (
              <div key={model.name} className="bg-zinc-900 p-4 rounded">
                <p className="font-bold">{model.name}</p>
                <p className="text-sm text-zinc-400">
                  {model.details?.parameter_size}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl mb-10">
        <h2 className="text-2xl mb-4">Available Nodes</h2>

        <div className="space-y-3">
          {nodes.map((node: any) => (
            <div key={node.id} className="bg-zinc-900 p-4 rounded">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-bold">{node.name}</p>
                  <p className="text-sm text-zinc-400">{node.gpu}</p>
                </div>

                <span
                  className={`px-3 py-1 rounded text-sm ${
                    node.status === "online" ? "bg-green-600" : "bg-red-600"
                  }`}
                >
                  {node.status}
                </span>
              </div>

              <p className="text-sm text-zinc-400 mt-3">
                Models: {node.models?.join(", ")}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl">
        <h2 className="text-2xl mb-4">Chat</h2>

        <textarea
          className="w-full bg-zinc-900 p-4 rounded text-white mb-4"
          rows={5}
          placeholder="Write your prompt..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />

        <button
          onClick={sendPrompt}
          disabled={loading}
          className="bg-blue-600 px-6 py-3 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Thinking..." : "Send"}
        </button>

        {response && (
          <div className="bg-zinc-900 p-4 rounded whitespace-pre-wrap mt-4">
            {response}
          </div>
        )}
      </section>
    </main>
  );
}
