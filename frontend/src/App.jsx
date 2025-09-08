import { useEffect, useState } from "react";
import {
  health,
  uploadStudentsCsv,
  runAllocation,
  latestRun,
  runResults,
  downloadCsv,
} from "./api";

export default function App() {
  const [apiOk, setApiOk] = useState(null);
  const [file, setFile] = useState(null);
  const [autoAlloc, setAutoAlloc] = useState(true);
  const [status, setStatus] = useState("");
  const [runId, setRunId] = useState("");
  const [results, setResults] = useState([]);

  useEffect(() => {
    health().then(() => setApiOk(true)).catch(() => setApiOk(false));
  }, []);

  const handleUpload = async () => {
    if (!file) { setStatus("Please choose a CSV first."); return; }
    setStatus("Uploading CSV & allocating...");
    try {
      const res = await uploadStudentsCsv(file, autoAlloc);
      setStatus(`Uploaded ${res.uploaded} students. run_id=${res.run_id ?? "—"}`);
      if (res.run_id) {
        setRunId(res.run_id);
        const rr = await runResults(res.run_id);
        setResults(rr.results || []);
        setStatus(s => `${s} | Allocation complete ✅`);
      }
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
  };

  const handleRun = async () => {
    setStatus("Running allocation...");
    try {
      const res = await runAllocation();
      setRunId(res.run_id);
      const rr = await runResults(res.run_id);
      setResults(rr.results || []);
      setStatus(`Allocation complete. run_id=${res.run_id}`);
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
  };

  const handleLatest = async () => {
    setStatus("Fetching latest run...");
    try {
      const { run_id } = await latestRun();
      setRunId(run_id);
      const rr = await runResults(run_id);
      setResults(rr.results || []);
      setStatus(`Loaded latest run: ${run_id}`);
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
  };

  const handleFetchRun = async () => {
    if (!runId) { setStatus("Enter a run_id first."); return; }
    setStatus(`Fetching results for run_id=${runId}...`);
    try {
      const rr = await runResults(runId);
      setResults(rr.results || []);
      setStatus(`Loaded ${rr.count} results for run ${runId}`);
    } catch (e) {
      setStatus(`Error: ${e.message}`);
    }
  };

  return (
    <div style={styles.wrap}>
      <h1 style={styles.h1}>PM Internship Allocation – Admin</h1>
      <div style={styles.card}>
        <div>API status: {apiOk === null ? "…" : apiOk ? "✅ OK" : "❌ Down"}</div>

        <div style={styles.section}>
          <h2 style={styles.h2}>1) Upload Students CSV</h2>
          <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <label style={{ marginLeft: 12 }}>
            <input type="checkbox" checked={autoAlloc} onChange={e => setAutoAlloc(e.target.checked)} />
            <span style={{ marginLeft: 6 }}>Auto-run allocation</span>
          </label>
          <button style={styles.btn} onClick={handleUpload}>Upload</button>
        </div>

        <div style={styles.section}>
          <h2 style={styles.h2}>2) Manual Allocation</h2>
          <button style={styles.btn} onClick={handleRun}>Run Allocation</button>
          <button style={styles.btn} onClick={handleLatest}>Load Latest</button>
        </div>

        <div style={styles.section}>
          <h2 style={styles.h2}>3) Results</h2>
          <div style={{ marginBottom: 8 }}>
            <input
              placeholder="run_id"
              value={runId}
              onChange={e => setRunId(e.target.value)}
              style={styles.input}
            />
            <button style={styles.btn} onClick={handleFetchRun}>Fetch</button>
            <button style={styles.btn} onClick={() => downloadCsv(runId)} disabled={!runId}>Download CSV</button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Email</th>
                  <th>Internship</th>
                  <th>Org</th>
                  <th>Location</th>
                  <th>Pincode</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td>{r.student_name}</td>
                    <td>{r.email}</td>
                    <td>{r.internship_title}</td>
                    <td>{r.organization}</td>
                    <td>{r.location}</td>
                    <td>{r.pincode}</td>
                    <td>{Number(r.final_score).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {results.length === 0 && <div style={{ marginTop: 8, color: "#666" }}>No results loaded yet.</div>}
          </div>
        </div>

        <div style={{ marginTop: 12, color: "#444" }}>{status}</div>
      </div>
      <p style={{ marginTop: 16, fontSize: 12, color: "#888" }}>API base: {import.meta.env.VITE_API_BASE}</p>
    </div>
  );
}

const styles = {
  wrap: { maxWidth: 1000, margin: "24px auto", padding: "0 16px", fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif" },
  h1: { fontSize: 22, marginBottom: 12 },
  card: { background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.05)" },
  section: { marginTop: 16 },
  h2: { fontSize: 18, marginBottom: 8 },
  btn: { marginLeft: 8, padding: "6px 10px", borderRadius: 8, border: "1px solid #ddd", background: "#f8f8f8", cursor: "pointer" },
  input: { padding: "6px 8px", borderRadius: 8, border: "1px solid #ddd", width: 120, marginRight: 8 },
  table: { width: "100%", borderCollapse: "collapse" }
};