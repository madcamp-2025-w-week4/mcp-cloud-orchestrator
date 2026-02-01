// ============================================================================
// MCP Cloud Orchestrator - Launch Wizard Component
// ============================================================================

import { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Check, Loader2, AlertTriangle } from 'lucide-react';
import { dashboardAPI, instanceAPI } from '../../api/client';

function LaunchWizard({ onClose, onComplete }) {
    const [step, setStep] = useState(1);
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [launching, setLaunching] = useState(false);

    // Cluster capacity state
    const [capacity, setCapacity] = useState({
        max_cpu: 4,
        max_memory_gb: 8,
        cpu_options: [1, 2, 4],
        memory_options: [2, 4, 8]
    });

    const [formData, setFormData] = useState({
        name: '',
        image: 'ubuntu:22.04',
        cpu: 1,
        memory: 2,
    });

    useEffect(() => {
        loadImages();
        loadCapacity();

        // Poll capacity every 5 seconds for reactive updates
        const interval = setInterval(loadCapacity, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadImages = async () => {
        setLoading(true);
        try {
            const response = await dashboardAPI.getImages();
            setImages(response.data);
        } catch (error) {
            console.error('Failed to load images:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadCapacity = async () => {
        try {
            const response = await dashboardAPI.getCapacity();
            setCapacity(response.data);

            // Adjust selected values if they exceed new capacity
            if (formData.cpu > response.data.max_cpu) {
                setFormData(prev => ({ ...prev, cpu: response.data.cpu_options[0] || 1 }));
            }
            if (formData.memory > response.data.max_memory_gb) {
                setFormData(prev => ({ ...prev, memory: response.data.memory_options[0] || 2 }));
            }
        } catch (error) {
            console.error('Failed to load capacity:', error);
        }
    };

    const handleLaunch = async () => {
        if (!formData.name.trim()) {
            alert('Please enter an instance name');
            return;
        }

        setLaunching(true);
        try {
            await instanceAPI.create(formData);
            onComplete();
        } catch (error) {
            console.error('Failed to launch instance:', error);
            alert('Failed to launch instance: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLaunching(false);
        }
    };

    const canProceed = () => {
        switch (step) {
            case 1:
                return formData.image !== '';
            case 2:
                return formData.cpu > 0 && formData.memory > 0;
            case 3:
                return formData.name.trim() !== '';
            default:
                return false;
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col animate-fadeIn">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50 flex-shrink-0">
                    <div>
                        <h2 className="text-lg font-semibold text-slate-800">Launch Instance</h2>
                        <p className="text-sm text-slate-500">Step {step} of 3</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Progress Bar */}
                <div className="h-1 bg-slate-200 flex-shrink-0">
                    <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${(step / 3) * 100}%` }}
                    />
                </div>

                {/* Content - Scrollable */}
                <div className="p-6 flex-1 overflow-y-auto min-h-0">
                    {/* Step 1: Select Image */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <div>
                                <h3 className="text-lg font-medium text-slate-800 mb-2">Select Image</h3>
                                <p className="text-sm text-slate-500">Choose a container image for your instance</p>
                            </div>

                            {loading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 gap-3 mt-4">
                                    {images.map((image) => (
                                        <button
                                            key={image.id}
                                            onClick={() => {
                                                setFormData({ ...formData, image: image.id });
                                                setStep(2); // Auto-advance to Step 2
                                            }}
                                            className={`p-4 border rounded-lg text-left transition-all ${formData.image === image.id
                                                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500/20'
                                                : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                                                }`}
                                        >
                                            <div className="font-medium text-slate-800">{image.name}</div>
                                            <div className="text-xs text-slate-500 mt-1">{image.description}</div>
                                            <div className="text-xs text-blue-600 mt-2 font-mono">{image.id}</div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 2: Configure Resources */}
                    {step === 2 && (
                        <div className="space-y-6">
                            <div>
                                <h3 className="text-lg font-medium text-slate-800 mb-2">Configure Resources</h3>
                                <p className="text-sm text-slate-500">Set the CPU and memory allocations</p>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="label">CPU Cores (max: {capacity.max_cpu})</label>
                                    <div className="flex items-center gap-3 flex-wrap">
                                        {capacity.cpu_options.map((value) => (
                                            <button
                                                key={value}
                                                onClick={() => setFormData({ ...formData, cpu: value })}
                                                className={`px-6 py-3 border rounded-lg font-medium transition-all ${formData.cpu === value
                                                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                                                    }`}
                                            >
                                                {value} vCPU
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="label">Memory (max: {capacity.max_memory_gb} GB)</label>
                                    <div className="flex items-center gap-3 flex-wrap">
                                        {capacity.memory_options.map((value) => (
                                            <button
                                                key={value}
                                                onClick={() => setFormData({ ...formData, memory: value })}
                                                className={`px-6 py-3 border rounded-lg font-medium transition-all ${formData.memory === value
                                                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                                                    }`}
                                            >
                                                {value} GB
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-slate-50 rounded-lg">
                                <div className="text-sm font-medium text-slate-700">Selected Configuration</div>
                                <div className="text-sm text-slate-500 mt-1">
                                    {formData.cpu} vCPU, {formData.memory} GB RAM
                                </div>
                            </div>

                            {/* Capacity info banner */}
                            <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                                <AlertTriangle className="w-4 h-4" />
                                <span>Resource options are limited based on available cluster capacity.</span>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Review & Launch */}
                    {step === 3 && (
                        <div className="space-y-6">
                            <div>
                                <h3 className="text-lg font-medium text-slate-800 mb-2">Review & Launch</h3>
                                <p className="text-sm text-slate-500">Give your instance a name and review the configuration</p>
                            </div>

                            <div>
                                <label className="label">Instance Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="input"
                                    placeholder="my-web-server"
                                    autoFocus
                                />
                            </div>

                            <div className="p-4 bg-slate-50 rounded-lg space-y-3">
                                <div className="text-sm font-medium text-slate-700">Instance Configuration</div>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <span className="text-slate-500">Image:</span>
                                        <span className="ml-2 font-mono text-slate-700">{formData.image}</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-500">Resources:</span>
                                        <span className="ml-2 text-slate-700">{formData.cpu} vCPU, {formData.memory} GB</span>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <div className="text-sm text-blue-800">
                                    <strong>Note:</strong> The instance will be assigned to an available worker node automatically.
                                    A unique port will be allocated for external access.
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer - Always visible */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50 flex-shrink-0">
                    <button
                        onClick={() => step > 1 ? setStep(step - 1) : onClose()}
                        className="btn btn-secondary flex items-center gap-2"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        {step > 1 ? 'Back' : 'Cancel'}
                    </button>

                    {step < 3 ? (
                        <button
                            onClick={() => setStep(step + 1)}
                            disabled={!canProceed()}
                            className="btn btn-primary flex items-center gap-2"
                        >
                            Next
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    ) : (
                        <button
                            onClick={handleLaunch}
                            disabled={!canProceed() || launching}
                            className="btn btn-success flex items-center gap-2"
                        >
                            {launching ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Launching...
                                </>
                            ) : (
                                <>
                                    <Check className="w-4 h-4" />
                                    Launch Instance
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

export default LaunchWizard;
