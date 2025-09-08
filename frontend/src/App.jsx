import { useEffect, useState } from "react";
import { Toaster, toast } from "react-hot-toast";
import {
  health,
  uploadStudentsCsv,
  runAllocation,
  latestRun,
  runResults,
  downloadCsv,
  listInternships,
} from "./api";

import Header from "./components/Header";
import UploadSection from "./components/UploadSection";
import ManualAllocationSection from "./components/ManualAllocationSection";
import ResultsTable from "./components/ResultsTable";
import InternshipsSection from "./components/InternshipsSection";
import NewJobModal from "./components/NewJobModal";

export default function App() {
  const [apiOk, setApiOk] = useState(null);
  const [file, setFile] = useState(null);
  const [autoAlloc, setAutoAlloc] = useState(true);
  const [mode, setMode] = useState("upsert");
  const [busy, setBusy] = useState(false);

  const [runId, setRunId] = useState("");
  const [results, setResults] = useState([]);
  const [uploadStats, setUploadStats] = useState(null);

  const [showNewJob, setShowNewJob] = useState(false);
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    health().then(() => setApiOk(true)).catch(() => setApiOk(false));
    listInternships().then((d) => setJobs(d.items || [])).catch(() => { });
  }, []);

  const handleUpload = async () => {
    if (!file) { toast.error("Choose a CSV first"); return; }
    setBusy(true);
    toast.loading("Uploading CSV…");
    try {
      const res = await uploadStudentsCsv(file, { autoAllocate: autoAlloc, mode });
      setUploadStats(res);
      toast.dismiss();
      toast.success(
        `Uploaded ${(res.uploaded_rows ?? res.uploaded) || 0} | inserted ${res.inserted ?? 0} | updated ${res.updated ?? 0} | skipped ${res.skipped ?? 0}`
      );
      if (res.run_id) {
        setRunId(String(res.run_id));
        const rr = await runResults(res.run_id);
        setResults(rr.results || []);
        toast.success(`Allocation complete (run ${res.run_id})`);
      }
    } catch (e) {
      toast.dismiss(); toast.error(parseErr(e));
    } finally {
      setBusy(false);
    }
  };

  const handleRun = async () => {
    setBusy(true);
    toast.loading("Running allocation…");
    try {
      const res = await runAllocation();
      setRunId(String(res.run_id));
      const rr = await runResults(res.run_id);
      setResults(rr.results || []);
      toast.dismiss(); toast.success(`Allocation complete (run ${res.run_id})`);
    } catch (e) {
      toast.dismiss(); toast.error(parseErr(e));
    } finally {
      setBusy(false);
    }
  };

  const handleLatest = async () => {
    setBusy(true);
    try {
      const { run_id } = await latestRun();
      if (!run_id) { toast("No runs yet"); return; }
      setRunId(String(run_id));
      const rr = await runResults(run_id);
      setResults(rr.results || []);
      toast.success(`Loaded latest run ${run_id}`);
    } catch (e) {
      toast.error(parseErr(e));
    } finally {
      setBusy(false);
    }
  };

  const handleFetchRun = async () => {
    if (!runId) { toast("Enter a run_id"); return; }
    setBusy(true);
    try {
      const rr = await runResults(runId);
      setResults(rr.results || []);
      toast.success(`Loaded ${rr.count ?? rr.results?.length ?? 0} results for run ${runId}`);
    } catch (e) {
      toast.error(parseErr(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50">
      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'white',
            color: '#374151',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          },
          success: {
            iconTheme: {
              primary: '#374151',
              secondary: 'white',
            },
          },
          error: {
            iconTheme: {
              primary: '#6b7280',
              secondary: 'white',
            },
          },
          loading: {
            iconTheme: {
              primary: '#9ca3af',
              secondary: 'white',
            },
          },
        }}
      />

      <Header apiOk={apiOk} />

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-10">
        <div className="space-y-8 sm:space-y-10 lg:space-y-12">

          {/* Upload Section */}
          <section className="bg-white rounded-xl border border-gray-200/60 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="mb-6 sm:mb-8">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-light text-gray-900 tracking-wide">
                  Student Data Upload
                </h2>
                <p className="text-sm sm:text-base text-gray-600 mt-2 font-light">
                  Upload CSV files containing student information and preferences
                </p>
              </div>

              <UploadSection
                file={file}
                setFile={setFile}
                mode={mode}
                setMode={setMode}
                autoAlloc={autoAlloc}
                setAutoAlloc={setAutoAlloc}
                onUpload={handleUpload}
                busy={busy}
                uploadStats={uploadStats}
              />
            </div>
          </section>

          {/* Manual Allocation Section */}
          <section className="bg-white rounded-xl border border-gray-200/60 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="mb-6 sm:mb-8">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-light text-gray-900 tracking-wide">
                  Allocation Management
                </h2>
                <p className="text-sm sm:text-base text-gray-600 mt-2 font-light">
                  Run allocation algorithms and manage assignment results
                </p>
              </div>

              <ManualAllocationSection
                runId={runId}
                setRunId={setRunId}
                onRun={handleRun}
                onLoadLatest={handleLatest}
                onFetch={handleFetchRun}
                onDownload={() => downloadCsv(runId)}
                busy={busy}
              />
            </div>
          </section>

          {/* Results Section */}
          {(results.length > 0 || runId) && (
            <section className="bg-white rounded-xl border border-gray-200/60 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="p-6 sm:p-8 lg:p-10">
                <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="text-lg sm:text-xl lg:text-2xl font-light text-gray-900 tracking-wide">
                      Allocation Results
                    </h2>
                    <p className="text-sm sm:text-base text-gray-600 mt-2 font-light">
                      {runId ? `Run ID: ${runId}` : 'Assignment results and statistics'}
                      {results.length > 0 && (
                        <span className="ml-2 text-gray-800 font-medium">
                          • {results.length} assignments
                        </span>
                      )}
                    </p>
                  </div>

                  {runId && (
                    <div className="flex items-center space-x-2 text-xs font-mono text-gray-500">
                      <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" />
                      <span className="uppercase tracking-wider">Active Run</span>
                    </div>
                  )}
                </div>

                <ResultsTable results={results} runId={runId} />
              </div>
            </section>
          )}

          {/* Internships Section */}
          <section className="bg-white rounded-xl border border-gray-200/60 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="mb-6 sm:mb-8">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-light text-gray-900 tracking-wide">
                  Available Internships
                </h2>
                <p className="text-sm sm:text-base text-gray-600 mt-2 font-light">
                  Manage internship opportunities and requirements
                  {jobs.length > 0 && (
                    <span className="ml-2 text-gray-800 font-medium">
                      • {jobs.length} positions
                    </span>
                  )}
                </p>
              </div>

              <InternshipsSection
                jobs={jobs}
                onAddClick={() => setShowNewJob(true)}
              />
            </div>
          </section>

        </div>
      </main>

      {/* Modal */}
      {showNewJob && (
        <div className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm flex items-center justify-center p-4">
          <NewJobModal
            onClose={() => setShowNewJob(false)}
            onCreated={async () => {
              const d = await listInternships();
              setJobs(d.items || []);
              setShowNewJob(false);
            }}
          />
        </div>
      )}
    </div>
  );
}

function parseErr(e) {
  try {
    return JSON.parse(e.message).detail || e.message;
  } catch {
    return e.message || "Error";
  }
}