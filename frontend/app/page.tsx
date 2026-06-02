import { QueryForm } from "../components/query-form";

type HealthResponse = {
  status: string;
  database_configured?: boolean;
};

async function getBackendHealth(): Promise<HealthResponse | null> {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${backendUrl}/api/v1/health`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }

    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getBackendHealth();
  const backendStatus = health?.status ?? "unreachable";
  const databaseConfigured = health?.database_configured ?? false;

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: 24,
        display: "grid",
        placeItems: "center",
        background:
          "radial-gradient(circle at top, rgba(255,255,255,0.9) 0%, rgba(245,239,230,0.95) 45%, #efe3d0 100%)",
      }}
    >
      <section
        style={{
          width: "min(920px, 100%)",
          display: "grid",
          gap: 24,
          padding: 28,
          borderRadius: 28,
          background: "rgba(255,255,255,0.72)",
          border: "1px solid rgba(31,41,55,0.08)",
          boxShadow: "0 24px 80px rgba(31,41,55,0.10)",
          backdropFilter: "blur(14px)",
        }}
      >
        <header style={{ display: "grid", gap: 10 }}>
          <p style={{ margin: 0, fontSize: 13, letterSpacing: 1.4, textTransform: "uppercase", color: "#8a6b4f" }}>
            Notesgram MVP
          </p>
          <h1 style={{ margin: 0, fontSize: "clamp(2rem, 5vw, 4rem)", lineHeight: 1.02 }}>
            Upload knowledge, ask questions, trace answers.
          </h1>
          <p style={{ margin: 0, maxWidth: 720, fontSize: 18, lineHeight: 1.65, color: "#4b5563" }}>
            Minimal frontend for the AI Knowledge Workspace MVP. The page checks backend health and offers a small query form for the retrieval flow.
          </p>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          <article style={{ padding: 18, borderRadius: 20, background: "#fffdf9", border: "1px solid #eadfce" }}>
            <p style={{ margin: 0, fontSize: 13, color: "#8a6b4f", textTransform: "uppercase", letterSpacing: 1.2 }}>
              Backend health
            </p>
            <p style={{ margin: "8px 0 0", fontSize: 28, fontWeight: 800 }}>{backendStatus}</p>
            <p style={{ margin: "8px 0 0", color: "#6b7280", lineHeight: 1.5 }}>
              The frontend checks <code>/api/v1/health</code> on the backend before rendering this status card.
            </p>
          </article>

          <article style={{ padding: 18, borderRadius: 20, background: "#fffdf9", border: "1px solid #eadfce" }}>
            <p style={{ margin: 0, fontSize: 13, color: "#8a6b4f", textTransform: "uppercase", letterSpacing: 1.2 }}>
              Database wiring
            </p>
            <p style={{ margin: "8px 0 0", fontSize: 28, fontWeight: 800 }}>{databaseConfigured ? "ready" : "pending"}</p>
            <p style={{ margin: "8px 0 0", color: "#6b7280", lineHeight: 1.5 }}>
              This indicates whether the backend has a <code>DATABASE_URL</code> configured in app state.
            </p>
          </article>
        </div>

        <section style={{ display: "grid", gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 24 }}>Query form</h2>
          <QueryForm />
        </section>
      </section>
    </main>
  );
}