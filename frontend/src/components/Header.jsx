export default function Header({ apiOk }) {
    return (
        <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-gray-200/60 shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4 lg:py-5">
                <div className="flex items-center justify-between">
                    {/* Main Title */}
                    <div className="flex flex-col min-w-0 flex-1">
                        <h1 className="text-lg sm:text-xl lg:text-2xl font-light tracking-wide text-gray-900 truncate">
                            PM Internship Allocation
                        </h1>
                        <span className="text-xs sm:text-xs lg:text-sm font-medium text-gray-500 uppercase tracking-widest mt-0.5 hidden sm:block">
                            Admin Dashboard
                        </span>
                    </div>

                    {/* API Status Indicator */}
                    <div className="flex items-center space-x-2 sm:space-x-3 lg:space-x-4 flex-shrink-0 ml-4">
                        {/* API Status Label - Hidden on mobile */}
                        <span className="text-xs font-medium text-gray-600 uppercase tracking-wide hidden md:block">
                            API Status
                        </span>
                        {/* Compact mobile label */}
                        <span className="text-xs font-medium text-gray-600 uppercase tracking-wide md:hidden">
                            API
                        </span>

                        <div className="flex items-center space-x-1.5 sm:space-x-2">
                            {/* Status Dot */}
                            <div className={`w-2 h-2 sm:w-2.5 sm:h-2.5 lg:w-3 lg:h-3 rounded-full ${apiOk === null
                                ? 'bg-gray-400 animate-pulse'
                                : apiOk
                                    ? 'bg-gray-800'
                                    : 'bg-gray-400'
                                }`} />
                            {/* Status Text */}
                            <span className={`text-xs sm:text-sm lg:text-sm font-mono ${apiOk === null
                                ? 'text-gray-500'
                                : apiOk
                                    ? 'text-gray-800 font-medium'
                                    : 'text-gray-500'
                                }`}>
                                {/* Abbreviated text on small screens */}
                                <span className="sm:hidden">
                                    {apiOk === null ? "..." : apiOk ? "OK" : "X"}
                                </span>
                                {/* Full text on larger screens */}
                                <span className="hidden sm:inline">
                                    {apiOk === null ? "Checking..." : apiOk ? "Connected" : "Offline"}
                                </span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}