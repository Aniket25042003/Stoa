import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <div className="card">
        <h1>GTM Agent</h1>
        <p style={{ color: "var(--muted)" }}>
          Autonomous market research, positioning, and GTM document generation.
        </p>
        <p>
          <Link className="btn" href="/login">
            Sign in
          </Link>{" "}
          <Link className="btn" href="/dashboard" style={{ marginLeft: 8, background: "transparent", border: "1px solid var(--border)", color: "var(--fg)" }}>
            Dashboard
          </Link>
        </p>
      </div>
    </main>
  );
}
