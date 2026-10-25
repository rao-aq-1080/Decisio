"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(email, password, name);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: "80px auto", padding: "0 20px" }}>
      <h1>Create your Decisio account</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text" placeholder="Name" value={name}
          onChange={(e) => setName(e.target.value)}
          style={inputStyle}
        />
        <input
          type="email" placeholder="Email" value={email} required
          onChange={(e) => setEmail(e.target.value)}
          style={inputStyle}
        />
        <input
          type="password" placeholder="Password" value={password} required minLength={6}
          onChange={(e) => setPassword(e.target.value)}
          style={inputStyle}
        />
        {error && <p style={{ color: "#f85149" }}>{error}</p>}
        <button type="submit" disabled={busy} style={buttonStyle}>
          {busy ? "Creating account..." : "Register"}
        </button>
      </form>
      <p style={{ color: "#8b949e", marginTop: 16 }}>
        Already have an account? <Link href="/login" style={{ color: "#2f81f7" }}>Log in</Link>
      </p>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  display: "block", width: "100%", padding: 10, marginBottom: 12,
  borderRadius: 6, border: "1px solid #2a333d", background: "#151b23", color: "#e6edf3",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 18px", borderRadius: 6, border: "none",
  background: "#2f81f7", color: "white", cursor: "pointer", width: "100%",
};
