type Props = {
  nodes: any[];
  models: any[];
};

export default function DashboardStats({ nodes, models }: Props) {
  return (
    <div className="grid grid-cols-5 gap-4 mb-8">
      <div className="bg-zinc-900 p-4 rounded">
        Nodes: {nodes.length}
      </div>

      <div className="bg-zinc-900 p-4 rounded">
        Online: {nodes.filter((n) => n.status === "online").length}
      </div>

      <div className="bg-zinc-900 p-4 rounded">
        GPUs: {nodes.filter((n) => n.gpu !== "CPU Mode").length}
      </div>

      <div className="bg-zinc-900 p-4 rounded">
        Users: 1
      </div>
    </div>
  );
}
