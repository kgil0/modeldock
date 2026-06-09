"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState("loading");
  const [models, setModels] = useState<any[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [streamingMessage, setStreamingMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [pullModelName, setPullModelName] = useState("");
  const [selectedModel, setSelectedModel] = useState("tinyllama:latest");
  const [selectedNode, setSelectedNode] = useState("local-node");
  const [detailNode, setDetailsNode] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [claimCode, setClaimCode] = useState("");
  const [claimLoading, setClaimLoading] = useState(false);  
  
  useEffect(() => {
    const savedLogin = localStorage.getItem("modeldock_logged_in");

    if (savedLogin === "true") {
      setLoggedIn(true);
    }
  }, []);

  async function loadData() {
    try {
      const statusRes = await fetch("/api/ollama/status");
      const statusData = await statusRes.json();

      const nodesRes = await fetch("/api/nodes?user_id=admin");
      const nodesData = await nodesRes.json();

      const historyRes = await fetch("/api/history");
      const historyData = await historyRes.json();

      setHistory(historyData);
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
      setStreamingMessage("");

      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          node_id: selectedNode,
          model: selectedModel,
          prompt: prompt,
        }),
      });

      const reader = res.body?.getReader();

      if (!reader) {
        setResponse("No response stream.");
        return;
      }

      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        fullText += chunk;

        setStreamingMessage(fullText);
      }

      setResponse(fullText);
      setStreamingMessage("");

    } catch {
      setResponse("Error talking to model.");
    }


    setLoading(false);
  }

  useEffect(() => {
    loadData();

    const interval = setInterval(() => {
      loadData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

if (!loggedIn) {
  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="bg-zinc-950 border border-zinc-800 p-8 rounded-xl w-[400px]">
        <h1 className="text-4xl font-bold mb-6">ModelDock</h1>

        <input
          type="email"
          placeholder="Email"
          value={loginEmail}
          onChange={(e) => setLoginEmail(e.target.value)}
          className="w-full bg-zinc-900 p-3 rounded mb-3"
        />

        <input
          type="password"
          placeholder="Password"
          value={loginPassword}
          onChange={(e) => setLoginPassword(e.target.value)}
          className="w-full bg-zinc-900 p-3 rounded mb-4"
        />

        <button
          onClick={async () => {
            const res = await fetch("/api/login", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                email: loginEmail,
                password: loginPassword,
              }),
            });
         
            const data = await res.json();

            if (data.status ==="ok") {
              setLoggedIn(true);
              localStorage.setItem("modeldock_logged_in", "true");
            }
          }}
          className="w-full bg-blue-600 p-3 rounded"
        >
          Login
        </button>
      </div>
    </main>
  );
}  

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-4xl font-bold">ModelDock</h1>

        <button
          onClick={() => {
            localStorage.removeItem("modeldock_logged_in");
            setLoggedIn(false);
          }}
          className="bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded"
        >
          Logout
        </button>
      </div>
      
      {detailNode && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">

          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-6 w-[600px]">

            <h2 className="text-2xl font-bold mb-4">
              {detailNode.name}
            </h2>

            <p>GPU: {detailNode.gpu_name || detailNode.gpu}</p>
            <p>CPU: {detailNode.cpu_percent}%</p>
            <p>RAM: {detailNode.ram_percent}%</p>
            <p>Disk: {detailNode.disk_percent}%</p>
            <p>Endpoint: {detailNode.endpoint}</p>
            <p>Last Seen: {detailNode.last_seen}</p>

            <p>
              Uptime: {Math.floor(detailNode.uptime_seconds / 3600)}h {Math.floor((detailNode.uptime_seconds % 3600) / 60)}m
            </p>

            <button
              onClick={() => setDetailsNode(null)}
              className="mt-4 bg-red-600 px-4 py-2 rounded"
            >
              Close
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-zinc-900 p-4 rounded">
          Nodes: {nodes.length}
        </div>

        <div className="bg-zinc-900 p-4 rounded">
          Online: {nodes.filter((n:any) => n.status === "online").length}
        </div>

        <div className="bg-zinc-900 p-4 rounded">
          Models: {models.length}
        </div>

        <div className="bg-zinc-900 p-4 rounded">
          Models: {models.length}
        </div>

        <div className="bg-zinc-900 p-4 rounded">
          GPUs: {nodes.filter((n:any) => n.gpu !== "CPU Mode").length}
        </div>
      </div>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl mb-10">
        <h2 className="text-2xl mb-4">Add Computer</h2>

        <p className="text-zinc-400 mb-4">
          Install ModelDock Agent on another comuter or GPU server.
        </p>

        <div className="mb-4">
          <button
            onClick={async () => {
              setClaimLoading(true);

              try {
                const res = await fetch("/api/generate-claim-code", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    user_id: "admin",
                  }),
                });

                const data = await res.json();

                if (data.code) {
                  setClaimCode(data.code);
                }     
              } finally {
                setClaimLoading(false);
              }
            }}
            className="bg-green-600 px-4 py-2 rounded"
          >
            {claimLoading ? "Generating..." : "Generate Claim Code"}
          </button>

          {claimCode && (
            <div className="mt-3 bg-zinc-900 p-3 rounded">
              <strong>Claim Code:</strong> {claimCode}
            </div>
          )}
        </div> 


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
              <div 
                key={model.name}
                className="bg-zinc-900 p-4 rounded flex justify-between items-center"
              >

                <div>
                  <p className="font-bold">{model.name}</p>
                  <p className="text-sm text-zinc-400">
                    {model.details?.parameter_size}
                  </p>
                </div>

                <button
                  onClick={async () => {
                    if (!confirm(`Delete ${model.name}?`)) return;

                    await fetch("/api/delete-model", {
                     method: "POST",
                     headers: {
                       "Content-Type": "application/json",
                     },
                     body: JSON.stringify({
                       model: model.name,
                     }),
                   });

                   loadData();
                 }}
                 className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
               >
                 Delete
               </button>
             </div>
           ))}

          </div>
        </section>
      </div>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl mb-10">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 mb-8">
        <h2 className="text-3xl font-bold mb-4">
          Pull New Model
        </h2>

        <div className="flex gap-4">
          <input
            type="text"
            placeholder="llama3"
            value={pullModelName}
            onChange={(e) => setPullModelName(e.target.value)}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg p-4 text-white"
          />

          <button
            onClick={async () => {
              if (!pullModelName) return;

              await fetch("/api/pull-model", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  model: pullModelName,
                }),
              }),

              alert("Model pull started");

              setTimeout(loadData, 5000);
            }}
            className="bg-green-600 hover:bg-green-700 px-6 rounded-lg"
          >
            Pull
          </button>
        </div>
      </div>

        <h2 className="text-2xl mb-4">Available Nodes</h2>

        <div className="space-y-3">
          {nodes.map((node: any) => (
            <div
              key={node.id}
              onClick={() => setDetailsNode(node)}
              className="bg-zinc-900 p-4 rounded cursor-pointer hover:bg-zinc-800"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-bold">{node.name}</p>
                  <p className="text-sm text-zinc-400">{node.gpu}</p>
                </div>

                <span
                  className={`px-3 py-1 rounded text-sm ${
                    node.status === "online" 
                      ? "bg-green-600"
                      : node.status === "stale"
                      ? "bg-yellow-600"
                      : "bg-red-600"
                  }`}
                >
                  {node.status}
                </span>
              </div>

              <p className="text-sm text-zinc-400 mt-3">
                Models: {node.models?.join(", ")}
              </p>
              
              <div className="grid grid-cols-4 gap-4 mt-4 text-sm">
                <div className="bg-zinc-800 p-3 rounded">
                  CPU : {node.cpu_percent}%
                </div>
     

                <div className="bg-zinc-800 p-3 rounded">
                  RAM: {node.ram_percent}%
                </div>

                <div className="bg-zinc-800 p-3 rounded">
                  Disk: {node.disk_percent}%
                </div>

                <div className="bg-zinc-800 p-3 rounded">
                  GPU: {node.gpu_name || node.gpu}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                <div className="bg-zinc-800 p-3 rounded">
                  VRAM: {node.gpu_memory_used ?? "-"} / {node.gpu_memory_total ?? "-"} MB
                </div>

                <div className="bg-zinc-800 p-3 rounded">
                  Temp: {node.gpu_temp ?? "-"}°C
                </div>

                <div className="bg-zinc-800 p-3 rounded">
                  Util: {node.gpu_util ?? "-"}%
                </div>
              </div>
                  
             
              <p className="text-sm text-zinc-500 mt-3">
                Endpoint: {node.endpoint}
              </p> 

            </div>
          ))}
        </div>
      </section>

      <section className="bg-zinc-950 border border-zinc-800 p-6 rounded-xl">
        <h2 className="text-2xl mb-4">Chat</h2>

        <select
          value={selectedNode}
          onChange={(e) => setSelectedNode(e.target.value)}
          className="w-full bg-zinc-900 p-4 rounded text-white mb-4"
        >
          {nodes.map((node: any) => (
            <option key={node.id} value={node.id}>
              {node.name}
            </option>
          ))}
        </select>

        <select

          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="w-full bg-zinc-900 p-4 rounded text-white mb-4"
        >

          {models.map((model: any) => (
            <option key={model.name} value={model.name}>
              {model.name}
            </option>
          ))}
        </select>

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

          <div className="mt-10">
            <h3 className="text-xl font-bold mb-4">
              Chat History
            </h3>

            <div className="space-y-4">
              {history.map((item: any, index: number) => (
                <div
                  key={index}
                  className="bg-zinc-900 border border-zinc-800 p-4 rounded-xl"
                >

                  <p className="text-xs text-zinc-500 mb-2">
                    {item.timestamp}
                  </p>

                  <p className="text-sm text-blue-400 mb-2">
                    Model: {item.model}
                  </p>

                  <p className="font-bold mb-2">
                    Prompt:
                  </p>

                  <p className="mb-4 whitespace-pre-wrap">
                    {item.prompt}
                  </p>

                  <p className="font-bold mb-2">
                    Response:
                  </p>

                  <p className="whitespace-pre-wrap text-zinc-300">
                    {item.response}
                  </p>
                </div>
              ))}
            </div>
          </div>  
      </section>
    </main>
  );
}
