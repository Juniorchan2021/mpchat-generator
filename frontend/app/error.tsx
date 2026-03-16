"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div style={{ padding: 40, color: "#fff", fontFamily: "monospace" }}>
      <h2 style={{ color: "#ff6b6b" }}>Client Error Caught</h2>
      <pre style={{ whiteSpace: "pre-wrap", background: "#1a1a2e", padding: 20, borderRadius: 8, fontSize: 14 }}>
        {error.message}
        {"\n\n"}
        {error.stack}
      </pre>
      <button
        onClick={reset}
        style={{ marginTop: 16, padding: "8px 20px", background: "#6c5ce7", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}
      >
        Retry
      </button>
    </div>
  );
}
