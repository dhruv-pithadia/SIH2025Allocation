export default function Select({ label, value, onChange, children, className = "", ...props }) {
    return (
        <label className={"text-sm " + className}>
            {label && <div className="text-slate-600 mb-1">{label}</div>}
            <select
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                className="text-sm border rounded-lg px-2 py-1.5 w-full"
                {...props}
            >
                {children}
            </select>
        </label>
    );
}