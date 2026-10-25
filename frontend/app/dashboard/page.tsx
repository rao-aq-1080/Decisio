"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

type MeetingListItem = { id: string; title: string; status: string };

const PAGE_SIZE = 8;

export default function DashboardPage() {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();

  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [page, setPage] = useState(1);
  const [fetching, setFetching] = useState(true);

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const [urlTitle, setUrlTitle] = useState("");
  const [url, setUrl] = useState("");
  const [submittingUrl, setSubmittingUrl] = useState(false);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<
    { meeting_id: string; title: string; text: string; score: number }[] | null
  >(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  async function loadMeetings(p: number) {
    if (!token) return;
    setFetching(true);
    const res = await apiFetch(`/meetings?page=${p}&page_size=${PAGE_SIZE}`, token);
    const data = await res.json();
    setMeetings(data);
    setFetching(false);
  }

  useEffect(() => {
    if (token) loadMeetings(page);
  }, [token, page]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !token) return;
    setUploading(true);

    const form = new FormData();
    form.append("title", title || file.name);
    form.append("file", file);

    const res = await apiFetch("/meetings/upload", token, { method: "POST", body: form });
    const meeting = await res.json();
    setUploading(false);
    setTitle("");
    setFile(null);
    router.push(`/meeting/${meeting.id}`);
  }

  async function handleUrlSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || !token) return;
    setSubmittingUrl(true);

    const res = await apiFetch("/meetings/from-url", token, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, title: urlTitle || "Untitled meeting" }),
    });
    const meeting = await res.json();
    setSubmittingUrl(false);
    setUrl("");
    setUrlTitle("");
    router.push(`/meeting/${meeting.id}`);
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || !token) return;
    setSearching(true);
    const res = await apiFetch(`/search?q=${encodeURIComponent(query)}`, token);
    const data = await res.json();
    setSearchResults(data.results);
    setSearching(false);
  }

  if (loading || !user) return null;

  return (
    <main style={{ maxWidth: 800, margin: "0 auto", padding: "48px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0 }}>🎙️ Decisio</h1>
          <p style={{ color: "#8b949e", margin: 0 }}>Welcome back, {user.name || user.email}</p>
        </div>
        <button onClick={logout} style={{ ...buttonStyle, background: "#21262d" }}>Log out</button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Link href="/chat" style={{ color: "#2f81f7" }}>💬 Chat with your meetings &rarr;</Link>
      </div>

      <form onSubmit={handleUpload} style={card}>
        <h3 style={{ marginTop: 0 }}>Upload a new meeting</h3>
        <input
          type="text" placeholder="Meeting title" value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={inputStyle}
        />
        <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <div style={{ marginTop: 12 }}>
          <button type="submit" disabled={!file || uploading} style={buttonStyle}>
            {uploading ? "Uploading..." : "Upload & Analyze"}
          </button>
        </div>
      </form>

      <form onSubmit={handleUrlSubmit} style={card}>
        <h3 style={{ marginTop: 0 }}>Or paste a link (YouTube, Google Drive, etc.)</h3>
        <p style={{ color: "#8b949e", fontSize: 13, marginTop: -8 }}>
          Good for large files — the server downloads it directly, nothing goes through your browser.
        </p>
        <input
          type="text" placeholder="Meeting title" value={urlTitle}
          onChange={(e) => setUrlTitle(e.target.value)}
          style={inputStyle}
        />
        <input
          type="url" placeholder="https://..." value={url} required
          onChange={(e) => setUrl(e.target.value)}
          style={inputStyle}
        />
        <button type="submit" disabled={!url.trim() || submittingUrl} style={buttonStyle}>
          {submittingUrl ? "Starting..." : "Fetch & Analyze"}
        </button>
      </form>

      <form onSubmit={handleSearch} style={card}>
        <h3 style={{ marginTop: 0 }}>Search across your meetings</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="text" placeholder="e.g. what did we decide about the mobile app?"
            value={query} onChange={(e) => setQuery(e.target.value)}
            style={{ ...inputStyle, marginBottom: 0, flex: 1 }}
          />
          <button type="submit" disabled={searching} style={buttonStyle}>
            {searching ? "Searching..." : "Search"}
          </button>
        </div>

        {searchResults !== null && (
          <div style={{ marginTop: 16 }}>
            {searchResults.length === 0 ? (
              <p style={{ color: "#8b949e" }}>No matching results found.</p>
            ) : (
              searchResults.map((r, i) => (
                <Link key={i} href={`/meeting/${r.meeting_id}`} style={{ textDecoration: "none", color: "inherit" }}>
                  <div style={{ padding: 12, borderTop: "1px solid #2a333d", cursor: "pointer" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <b>{r.title}</b>
                      <span style={{ color: "#8b949e", fontSize: 12 }}>{r.score.toFixed(2)}</span>
                    </div>
                    <p style={{ color: "#8b949e", margin: "4px 0 0" }}>{r.text}</p>
                  </div>
                </Link>
              ))
            )}
          </div>
        )}
      </form>

      <h2>Meeting history</h2>
      {fetching ? (
        <p style={{ color: "#8b949e" }}>Loading...</p>
      ) : meetings.length === 0 ? (
        <p style={{ color: "#8b949e" }}>No meetings yet — upload one above to get started.</p>
      ) : (
        <div>
          {meetings.map((m) => (
            <Link key={m.id} href={`/meeting/${m.id}`} style={{ textDecoration: "none", color: "inherit" }}>
              <div style={{ ...card, display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}>
                <span>{m.title}</span>
                <span style={{ color: "#8b949e", fontSize: 13 }}>{m.status}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button
          disabled={page === 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          style={{ ...buttonStyle, background: "#21262d" }}
        >
          Previous
        </button>
        <button
          disabled={meetings.length < PAGE_SIZE}
          onClick={() => setPage((p) => p + 1)}
          style={{ ...buttonStyle, background: "#21262d" }}
        >
          Next
        </button>
      </div>
    </main>
  );
}

const card: React.CSSProperties = {
  background: "#151b23", border: "1px solid #2a333d", borderRadius: 10,
  padding: 20, marginBottom: 12,
};

const inputStyle: React.CSSProperties = {
  display: "block", width: "100%", padding: 10, marginBottom: 12,
  borderRadius: 6, border: "1px solid #2a333d", background: "#0b0f14", color: "#e6edf3",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 18px", borderRadius: 6, border: "none",
  background: "#2f81f7", color: "white", cursor: "pointer",
};
