import Button from "./ui/Button";
import { TextInput } from "./ui/Input";

export default function ManualAllocationSection({
    runId, setRunId,
    onRun, onLoadLatest, onFetch, onDownload,
    busy
}) {
    return (
        <section className="bg-white rounded-xl border shadow-sm p-4">
            <h2 className="text-base font-semibold mb-3">2) Manual Allocation</h2>
            <div className="flex flex-wrap items-center gap-2">
                <Button onClick={onRun} disabled={busy}>Run Allocation</Button>
                <Button onClick={onLoadLatest} disabled={busy}>Load Latest</Button>
                <TextInput
                    placeholder="run_id"
                    value={runId}
                    onChange={setRunId}
                    className="w-28"
                />
                <Button onClick={onFetch} disabled={!runId || busy}>Fetch</Button>
                <Button onClick={onDownload} disabled={!runId}>Download CSV</Button>
            </div>
        </section>
    );
}