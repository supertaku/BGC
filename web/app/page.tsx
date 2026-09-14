import SceneViewer from "@/components/SceneViewer";

export default function Home() {
  return (
    <main>
      <header className="status-panel">
        <p className="eyebrow">M11 · geographic massing diagnostic</p>
        <h1>Whole-BGC low-fidelity skeleton</h1>
        <p>Real footprints · evidence-aware heights · 250 m tiles · seven preserved LOD1 landmarks</p>
      </header>
      <SceneViewer />
    </main>
  );
}
