async function getOllamaStatus() {
	try {
		const res = await fetch("http://127.0.0.1:8000/ollama/status", {
			cache: "no-store",
		});

		return await res.json();
	       }catch (error) {
		return {
			status: "error",
			models: [],
		       };
	       }
         }

	export default async function Home() {
		const data = await getOllamaStatus();

		return (
			<main className="min-h-screen bg-black text-white p-10">
				<h1 className="text-4xl font-bold mb-8">ModelDock</h1>
				<div className="mb-6">
					<h2 className="text-2xl mb-2">Ollama Status</h2>

					<div
						className={`inline-block px-4 py-2 rounded ${
							data.status === "connected"
								?"bg-green-600"
								:"bg-red-600"
						}`}
				>
					{data.status}
				</div>
			</div>

			<div>
				<h2 className="text-2xl mb-4">Installed Models</h2>

				<div className="space-y-2">
					{data.models?.map((model: any) => (
						<div
							key={model.name}
							className="bg-zinc-900 p-4 rounded"
						>
							<p className="font-bold">{model.name}</p>
							<p className="text-sm text-zinc-400">
								{model.details?.parameter_size}
							</p>
						</div>
					))}
				</div>
			</div>
		</main>
	);
}
					
		
