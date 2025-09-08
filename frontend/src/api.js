const API = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function health() {
    const r = await fetch(`${API}/health`);
    if (!r.ok) throw new Error("API down");
    return r.json();
}

export async function uploadStudentsCsv(file, { autoAllocate = true, mode = "upsert" } = {}) {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${API}/upload/students?auto_allocate=${autoAllocate}&mode=${mode}`, {
        method: "POST",
        body: fd,
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function runAllocation() {
    const r = await fetch(`${API}/run`, { method: "POST" });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function latestRun() {
    const r = await fetch(`${API}/runs/latest`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function runResults(runId) {
    const r = await fetch(`${API}/runs/${runId}/results`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export function downloadCsv(runId) {
    if (!runId) return;
    window.open(`${API}/download/${runId}.csv`, "_blank");
}

export async function createInternship(payload) {
    const r = await fetch(`${API}/internships`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function listInternships() {
    const r = await fetch(`${API}/internships`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}