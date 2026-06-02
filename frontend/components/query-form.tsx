"use client";

import type { FormEvent } from "react";
import { useState } from "react";

export function QueryForm() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedQuery(query.trim() || null);
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
      <label style={{ display: "grid", gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>Ask a question</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="What does the document say about embeddings?"
          style={{
            border: "1px solid #d6c6b2",
            borderRadius: 14,
            padding: "14px 16px",
            fontSize: 16,
            background: "#fffdf9",
          }}
        />
      </label>

      <button
        type="submit"
        style={{
          border: 0,
          borderRadius: 999,
          padding: "12px 18px",
          background: "#1f2937",
          color: "white",
          fontWeight: 700,
          width: "fit-content",
          cursor: "pointer",
        }}
      >
        Prepare query
      </button>

      <div
        style={{
          minHeight: 56,
          padding: 16,
          borderRadius: 16,
          background: "#fff",
          border: "1px solid #eadfce",
        }}
      >
        {submittedQuery ? (
          <p style={{ margin: 0, lineHeight: 1.5 }}>
            Query ready: <strong>{submittedQuery}</strong>
          </p>
        ) : (
          <p style={{ margin: 0, lineHeight: 1.5, color: "#6b7280" }}>
            Enter a question to prepare a retrieval query.
          </p>
        )}
      </div>
    </form>
  );
}