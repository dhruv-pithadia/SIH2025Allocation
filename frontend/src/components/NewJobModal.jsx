import { useState } from "react";
import Button from "./ui/Button";
import { TextInput, NumberInput } from "./ui/Input";
import { createInternship } from "../api";
import { toast } from "react-hot-toast";

export default function NewJobModal({ onClose, onCreated }) {
    const [form, setForm] = useState({
        org_name: "",
        title: "",
        location: "",
        pincode: "",
        capacity: 1,
        min_cgpa: 0,
        req_skills_text: "",
    });
    const [busy, setBusy] = useState(false);

    const save = async () => {
        if (!form.org_name || !form.title) { toast.error("Org and Title required"); return; }
        setBusy(true);
        try {
            await createInternship(form);
            toast.success("Internship created");
            onCreated?.();
        } catch (e) {
            toast.error(parseErr(e));
        } finally { setBusy(false); }
    };

    return (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl w-full max-w-lg p-4 border shadow-lg">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">Add Internship</h3>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-700">✕</button>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <TextInput label="Org Name" value={form.org_name} onChange={v => setForm(f => ({ ...f, org_name: v }))} />
                    <TextInput label="Title" value={form.title} onChange={v => setForm(f => ({ ...f, title: v }))} />
                    <TextInput label="Location" value={form.location} onChange={v => setForm(f => ({ ...f, location: v }))} />
                    <TextInput label="Pincode" value={form.pincode} onChange={v => setForm(f => ({ ...f, pincode: v }))} />
                    <NumberInput label="Capacity" value={form.capacity} onChange={v => setForm(f => ({ ...f, capacity: v }))} />
                    <NumberInput label="Min CGPA" value={form.min_cgpa} step="0.1" onChange={v => setForm(f => ({ ...f, min_cgpa: v }))} />
                    <div className="col-span-2">
                        <TextInput label="Required Skills (free text)" value={form.req_skills_text} onChange={v => setForm(f => ({ ...f, req_skills_text: v }))} />
                    </div>
                </div>

                <div className="mt-4 flex justify-end gap-2">
                    <Button onClick={onClose}>Cancel</Button>
                    <Button onClick={save} disabled={busy} className="bg-emerald-600 text-white border-emerald-600">
                        {busy ? "Saving…" : "Create"}
                    </Button>
                </div>
            </div>
        </div>
    );
}

function parseErr(e) {
    try { return JSON.parse(e.message).detail || e.message; } catch { return e.message || "Error"; }
}