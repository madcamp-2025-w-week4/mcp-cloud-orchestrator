// ============================================================================
// MCP Cloud Orchestrator - Web Terminal Component
// ============================================================================
// xterm.js 기반 WebSocket 터미널

import { useEffect, useRef, useState } from 'react';
import { Terminal } from 'lucide-react';

function WebTerminal({ instanceId, onClose }) {
    const terminalRef = useRef(null);
    const terminalInstance = useRef(null);
    const wsRef = useRef(null);
    const fitAddonRef = useRef(null);
    const [status, setStatus] = useState('connecting');
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;

        const initTerminal = async () => {
            try {
                // Dynamically import xterm (loaded via CDN in index.html)
                // If xterm is loaded via CDN, it will be available globally
                if (!window.Terminal) {
                    // Try to load from CDN
                    await loadXtermFromCDN();
                }

                if (!mounted) return;

                // Create terminal instance
                const term = new window.Terminal({
                    cursorBlink: true,
                    theme: {
                        background: '#1e1e2e',
                        foreground: '#cdd6f4',
                        cursor: '#f5e0dc',
                        cursorAccent: '#1e1e2e',
                        selection: '#585b70',
                        black: '#45475a',
                        red: '#f38ba8',
                        green: '#a6e3a1',
                        yellow: '#f9e2af',
                        blue: '#89b4fa',
                        magenta: '#f5c2e7',
                        cyan: '#94e2d5',
                        white: '#bac2de',
                        brightBlack: '#585b70',
                        brightRed: '#f38ba8',
                        brightGreen: '#a6e3a1',
                        brightYellow: '#f9e2af',
                        brightBlue: '#89b4fa',
                        brightMagenta: '#f5c2e7',
                        brightCyan: '#94e2d5',
                        brightWhite: '#a6adc8',
                    },
                    fontFamily: '"JetBrains Mono", "Fira Code", "Consolas", monospace',
                    fontSize: 14,
                    lineHeight: 1.2,
                    convertEol: true,
                });

                terminalInstance.current = term;

                // Open terminal
                if (terminalRef.current) {
                    term.open(terminalRef.current);

                    // Fit addon
                    if (window.FitAddon) {
                        const fitAddon = new window.FitAddon.FitAddon();
                        term.loadAddon(fitAddon);
                        fitAddonRef.current = fitAddon;
                        fitAddon.fit();
                    }
                }

                // Connect WebSocket
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${instanceId}`;

                const ws = new WebSocket(wsUrl);
                wsRef.current = ws;

                ws.onopen = () => {
                    if (mounted) {
                        setStatus('connected');
                        term.write('\r\n\x1b[32m✓ Connected to container\x1b[0m\r\n\r\n');
                    }
                };

                ws.onmessage = (event) => {
                    if (event.data instanceof Blob) {
                        event.data.text().then(text => term.write(text));
                    } else {
                        term.write(event.data);
                    }
                };

                ws.onerror = (err) => {
                    console.error('WebSocket error:', err);
                    if (mounted) {
                        setStatus('error');
                        setError('Connection failed');
                        term.write('\r\n\x1b[31m✗ Connection error\x1b[0m\r\n');
                    }
                };

                ws.onclose = (event) => {
                    if (mounted) {
                        setStatus('disconnected');
                        term.write('\r\n\x1b[33m⚠ Disconnected\x1b[0m\r\n');
                    }
                };

                // Handle terminal input
                term.onData((data) => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(data);
                    }
                });

                // Handle resize
                const handleResize = () => {
                    if (fitAddonRef.current) {
                        fitAddonRef.current.fit();
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: 'resize',
                                rows: term.rows,
                                cols: term.cols
                            }));
                        }
                    }
                };

                window.addEventListener('resize', handleResize);

            } catch (err) {
                console.error('Failed to initialize terminal:', err);
                if (mounted) {
                    setStatus('error');
                    setError(err.message);
                }
            }
        };

        initTerminal();

        return () => {
            mounted = false;
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (terminalInstance.current) {
                terminalInstance.current.dispose();
            }
        };
    }, [instanceId]);

    // Load xterm from CDN
    const loadXtermFromCDN = () => {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (window.Terminal) {
                resolve();
                return;
            }

            // Load xterm CSS
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css';
            document.head.appendChild(css);

            // Load xterm JS
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js';
            script.onload = () => {
                // Load fit addon
                const fitScript = document.createElement('script');
                fitScript.src = 'https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js';
                fitScript.onload = resolve;
                fitScript.onerror = reject;
                document.head.appendChild(fitScript);
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 animate-fadeIn">
            <div className="bg-slate-900 rounded-xl shadow-2xl w-[90vw] h-[80vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                        <Terminal className="w-5 h-5 text-green-400" />
                        <span className="text-white font-medium">Terminal - {instanceId}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${status === 'connected' ? 'bg-green-500/20 text-green-400' :
                                status === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' :
                                    status === 'error' ? 'bg-red-500/20 text-red-400' :
                                        'bg-slate-500/20 text-slate-400'
                            }`}>
                            {status}
                        </span>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white px-3 py-1 rounded hover:bg-slate-700"
                    >
                        Close
                    </button>
                </div>

                {/* Terminal Container */}
                <div
                    ref={terminalRef}
                    className="flex-1 p-2"
                    style={{ backgroundColor: '#1e1e2e' }}
                />

                {/* Error Display */}
                {error && (
                    <div className="px-4 py-2 bg-red-500/10 border-t border-red-500/30 text-red-400 text-sm">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}

export default WebTerminal;
