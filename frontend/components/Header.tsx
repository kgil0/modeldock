type HeaderProps = {
  onLogout: () => void;
};

export default function Header({ onLogout }: HeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      <h1 className="text-4xl font-bold">ModelDock</h1>

      <button
        onClick={onLogout}
        className="bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded"
      >
        Logout
      </button>
    </div>
  );
}
