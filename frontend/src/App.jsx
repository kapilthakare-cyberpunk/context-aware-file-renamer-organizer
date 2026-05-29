import { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [targetDir, setTargetDir] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [log, setLog] = useState('');
  const [dryRun, setDryRun] = useState(true);
  const [recursive, setRecursive] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const buttonRef = useRef(null);

  useEffect(() => {
    const button = buttonRef.current;
    if (!button) return;

    const handleMouseMove = (e) => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const distance = Math.min(Math.sqrt(x * x + y * y), 50);
      const scale = 1 + (distance * 0.05) / 50;
      const translateX = (x * distance * 0.1) / 50;
      const translateY = (y * distance * 0.1) / 50;
      
      button.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    };

    const handleMouseLeave = () => {
      button.style.transform = '';
    };

    button.addEventListener('mousemove', handleMouseMove);
    button.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      button.removeEventListener('mousemove', handleMouseMove);
      button.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  const handleOrganize = async () => {
    if (!targetDir.trim()) {
      setShowLog(true);
      setLog('Please select a target directory');
      return;
    }

    setIsRunning(true);
    setLog('Starting organization...\n');
    setShowLog(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/organize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_dir: targetDir,
          dry_run: dryRun,
          recursive: recursive,
        }),
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`Server error: ${err}`);
      }

      const data = await response.json();
      setLog((prev) => prev + data.log + '\nOrganization complete!');
    } catch (e) {
      setLog((prev) => prev + `Error: ${e.message}\n`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSelectDirectory = async () => {
    try {
      const { value } = await window.__TAURI__.dialog.open({
        directory: true,
        multiple: false,
      });
      if (value) setTargetDir(value);
    } catch {
      setTargetDir('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-6">
      <div className="relative w-full max-w-2xl">
        <div className="absolute inset-0 bg-white/5 backdrop-blur-xl rounded-3xl shadow-2xl shadow-cyan-500/10 border border-white/10"></div>
        
        <div className="relative z-10 p-12 md:p-16">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-black text-white mb-4 tracking-tight leading-none">
              File Organizer
            </h1>
            <p className="text-lg text-gray-400 font-medium max-w-md mx-auto">
              Organize your files intelligently with context-aware sorting
            </p>
          </div>

          <div className="space-y-8">
            <div>
              <label className="block text-xs font-bold text-cyan-400 uppercase tracking-widest mb-3">
                Target Directory
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={targetDir}
                  onChange={(e) => setTargetDir(e.target.value)}
                  placeholder="/Users/username/Downloads"
                  className="flex-1 px-5 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400/50 transition-all"
                />
                <button
                  onClick={handleSelectDirectory}
                  className="px-6 py-4 bg-cyan-500/20 border border-cyan-400/30 rounded-xl text-cyan-300 font-medium hover:bg-cyan-500/30 transition-colors"
                >
                  Browse
                </button>
              </div>
            </div>

            <div className="flex gap-8">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="w-5 h-5 text-cyan-400 border-white/20 rounded bg-white/5 focus:ring-cyan-400/50 focus:ring-2"
                />
                <span className="ml-3 text-gray-300 font-medium">Dry Run</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={recursive}
                  onChange={(e) => setRecursive(e.target.checked)}
                  className="w-5 h-5 text-cyan-400 border-white/20 rounded bg-white/5 focus:ring-cyan-400/50 focus:ring-2"
                />
                <span className="ml-3 text-gray-300 font-medium">Recursive</span>
              </label>
            </div>

            <button
              ref={buttonRef}
              onClick={handleOrganize}
              disabled={isRunning}
              className="w-full py-5 px-6 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-xl font-bold text-lg hover:from-cyan-400 hover:to-cyan-500 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-cyan-500/25"
            >
              {isRunning ? 'Organizing...' : 'Organize Now'}
            </button>
          </div>

          {showLog && (
            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl blur-xl"></div>
                <textarea
                  value={log}
                  onChange={(e) => setLog(e.target.value)}
                  className="relative w-full h-56 px-5 py-4 bg-white/5 border border-white/10 rounded-xl font-mono text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyan-400/30 transition-all resize-none"
                  readOnly
                />
              </div>
            </div>
          )}

          <p className="text-xs text-gray-500 mt-8 text-center font-medium">
            Protected: .ssh • .git • node_modules • README • LICENSE
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;