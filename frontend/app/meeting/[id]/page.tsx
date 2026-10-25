"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

type Meeting = {
  id: string;
  title: string;
  status: string;
  transcript?: string;
  summary?: string;
  decisions?: { decision: string; made_by: string }[];
  action_items?: { task: string; owner: string; deadline: string }[];
  open_debates?: { topic: string; positions: string[] }[];
};

export default function MeetingPage() {
  const { id } = useParams<{ id: string }>();
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  async function fetchMeeting() {
    if (!token) return;
    const res = await apiFetch(`/meetings/${id}`, token);
    if (res.ok) setMeeting(await res.json());
  }

  useEffect(() => {
    if (token) fetchMeeting();
  }, [token, id]);

  useEffect(() => {
    if (!meeting || meeting.status === "done" || meeting.status === "failed") return;
    pollRef.current = setInterval(fetchMeeting, 3000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [meeting]);

  if (loading || !user || !meeting) return null;

  return (
    <main style={{ maxWidth: 800, margin: "0 auto", padding: "48px 20px" }}>
      <Link href="/dashboard" style={{ color: "#2f81f7" }}>&larr; Back to dashboard</Link>

      <div style={card}>
        <h1 style={{ marginTop: 0 }}>{meeting.title}</h1>
        <p>
          Status: <b>{meeting.status}</b>
          {meeting.status !== "done" && meeting.status !== "failed" && " — processing..."}
        </p>

        {meeting.summary && (
          <>
            <h3>Summary</h3>
            <p>{meeting.summary}</p>
          </>
        )}

        {meeting.decisions && meeting.decisions.length > 0 && (
          <>
            <h3>Decisions</h3>
            <ul>
              {meeting.decisions.map((d, i) => (
                <li key={i}>{d.decision} <span style={{ color: "#8b949e" }}>— {d.made_by}</span></li>
              ))}
            </ul>
          </>
        )}

        {meeting.action_items && meeting.action_items.length > 0 && (
          <>
            <h3>Action Items</h3>
            <ul>
              {meeting.action_items.map((a, i) => (
                <li key={i}>
                  {a.task} <span style={{ color: "#8b949e" }}>— {a.owner}, due {a.deadline}</span>
                </li>
              ))}
            </ul>
          </>
        )}

        {meeting.open_debates && meeting.open_debates.length > 0 && (
          <>
            <h3>Open Debates</h3>
            <ul>
              {meeting.open_debates.map((d, i) => (
                <li key={i}>{d.topic}: {d.positions.join(" vs. ")}</li>
              ))}
            </ul>
          </>
        )}

        {meeting.transcript && (
          <details style={{ marginTop: 16 }}>
            <summary style={{ cursor: "pointer", color: "#8b949e" }}>Raw transcript</summary>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, color: "#8b949e" }}>{meeting.transcript}</pre>
          </details>
        )}
      </div>
    </main>
  );
}

const card: React.CSSProperties = {
  background: "#151b23", border: "1px solid #2a333d", borderRadius: 10,
  padding: 20, marginTop: 20,
};
