export function TextInput({ label, value, onChange, placeholder, className = "", ...props }) {
    return (
        <label className={"text-sm " + className}>
            {label && <div className="text-slate-600 mb-1">{label}</div>}
            <input
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                placeholder={placeholder}
                className="w-full px-2 py-1.5 border rounded-lg"
                {...props}
            />
        </label>
    );
}

export function NumberInput({ label, value, onChange, step = "1", className = "", ...props }) {
    return (
        <label className={"text-sm " + className}>
            {label && <div className="text-slate-600 mb-1">{label}</div>}
            <input
                type="number"
                step={step}
                value={value}
                onChange={(e) => onChange?.(Number(e.target.value))}
                className="w-full px-2 py-1.5 border rounded-lg"
                {...props}
            />
        </label>
    );
}