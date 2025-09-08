export default function ResultsTable({ results, runId }) {
    return (
        <section className="bg-white rounded-xl border shadow-sm p-0">
            <div className="p-4 flex items-center justify-between">
                <h2 className="text-base font-semibold">
                    3) Results {runId ? <span className="text-slate-500 font-normal">(run {runId})</span> : null}
                </h2>
                <span className="text-xs text-slate-500">{results?.length ?? 0} rows</span>
            </div>
            <div className="overflow-auto max-h-[60vh]">
                <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-slate-100">
                        <tr className="[&>th]:text-left [&>th]:px-3 [&>th]:py-2 [&>th]:font-medium">
                            <th>Student</th>
                            <th>Email</th>
                            <th>Internship</th>
                            <th>Org</th>
                            <th>Location</th>
                            <th>Pincode</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody className="[&>tr:hover]:bg-slate-50">
                        {results.map((r, i) => (
                            <tr key={i} className="[&>td]:px-3 [&>td]:py-2 border-t">
                                <td className="font-medium">{r.student_name}</td>
                                <td className="text-slate-600">{r.email}</td>
                                <td>{r.internship_title}</td>
                                <td>{r.organization}</td>
                                <td>{r.location}</td>
                                <td className="tabular-nums">{r.pincode}</td>
                                <td className="tabular-nums">{Number(r.final_score).toFixed(4)}</td>
                            </tr>
                        ))}
                        {(!results || results.length === 0) && (
                            <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">No results loaded.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}