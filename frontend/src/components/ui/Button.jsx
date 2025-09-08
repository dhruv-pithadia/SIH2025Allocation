export default function Button({ children, className = "", ...props }) {
    return (
        <button
            className={
                "px-3 py-1.5 rounded-lg border text-sm disabled:opacity-50 " + className
            }
            {...props}
        >
            {children}
        </button>
    );
}