import Button from "./ui/Button";
import Select from "./ui/Select";

export default function UploadSection({
    file,
    setFile,
    mode,
    setMode,
    autoAlloc,
    setAutoAlloc,
    onUpload,
    busy,
    uploadStats,
}) {
    return (
        <section className="bg-white rounded-xl border shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold">1) Upload Students CSV</h2>
                <div className="flex gap-3">
                    <Select value={mode} onChange={setMode}>
                        <option value="upsert">Upsert</option>
                        <option value="skip">Skip Duplicates</option>
                        <option value="replace_all">Replace All</option>
                    </Select>
                    <label className="text-sm flex items-center gap-2">
                        <input type="checkbox" checked={autoAlloc} onChange={e => setAutoAlloc(e.target.checked)} />
                        Auto allocate
                    </label>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
                <input
                    type="file"
                    accept=".csv"
                    onChange={e => setFile(e.target.files?.[0] || null)}
                    className="text-sm file:mr-3 file:px-3 file:py-1.5 file:rounded-lg file:border file:bg-white file:hover:bg-gray-50"
                />
                <Button onClick={onUpload} disabled={!file || busy} className="bg-blue-600 text-white border-blue-600">
                    {busy ? "Working…" : "Upload"}
                </Button>

                {uploadStats && (
                    <div className="text-xs text-slate-600">
                        Uploaded: <b>{uploadStats.uploaded_rows ?? uploadStats.uploaded}</b> •
                        Inserted: <b>{uploadStats.inserted}</b> •
                        Updated: <b>{uploadStats.updated}</b> •
                        Skipped: <b>{uploadStats.skipped}</b> •
                        Run: <b>{uploadStats.run_id ?? "—"}</b>
                    </div>
                )}
            </div>
        </section>
    );
}