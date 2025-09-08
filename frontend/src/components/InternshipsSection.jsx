import Button from "./ui/Button";

export default function InternshipsSection({ jobs, onAddClick }) {
    return (
        <section className="bg-white rounded-xl border shadow-sm p-4">
            <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold">4) Internships</h2>
                <Button onClick={onAddClick} className="bg-emerald-600 text-white border-emerald-600">
                    + Add Internship
                </Button>
            </div>
            <div className="mt-3 overflow-auto">
                <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                        <tr className="[&>th]:text-left [&>th]:px-3 [&>th]:py-2 [&>th]:font-medium">
                            <th>ID</th><th>Org</th><th>Title</th><th>Loc</th><th>Pin</th><th>Cap</th><th>Min CGPA</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map(j => (
                            <tr key={j.internship_id} className="[&>td]:px-3 [&>td]:py-2 border-t">
                                <td>{j.internship_id}</td>
                                <td>{j.org_name}</td>
                                <td className="font-medium">{j.title}</td>
                                <td>{j.location}</td>
                                <td>{j.pincode}</td>
                                <td>{j.capacity}</td>
                                <td>{j.min_cgpa}</td>
                            </tr>
                        ))}
                        {jobs.length === 0 && (
                            <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">No internships yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}