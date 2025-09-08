const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function health() {
    const r = await fetch(`${API_BASE}/health`);
    return r.json();
}

export async function uploadStudentsCsv(file, autoAllocate = true) {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch(`${API_BASE}/upload/students?auto_allocate=${autoAllocate}`, {
        method: "POST",
        body: form,
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function runAllocation() {
    const r = await fetch(`${API_BASE}/run`, { method: "POST" });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function latestRun() {
    const r = await fetch(`${API_BASE}/run/latest`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export async function runResults(runId) {
    const r = await fetch(`${API_BASE}/run/${runId}/results`);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

export function downloadCsv(runId) {
    window.location.href = `${API_BASE}/download/${runId}.csv`;
}