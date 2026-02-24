
import { useRef, useState } from 'react';
import SignatureCanvas from 'react-signature-canvas';
import { useMutation, useQuery } from '@tanstack/react-query';
import { signatureAPI, contractsAPI } from '../services/api';
import { PenTool, Undo, ShieldCheck, History, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ESignature() {
    const sigCanvas = useRef<any>(null);
    const [trimmedDataURL, setTrimmedDataURL] = useState<string | null>(null);
    const [selectedContractId] = useState<string>('c1'); // Mock selection
    const [signerName] = useState('John Doe'); // Mock user

    const { data: _contractsData } = useQuery({ queryKey: ['contracts'], queryFn: () => contractsAPI.list() });
    const { data: auditData } = useQuery({
        queryKey: ['audit-trail', selectedContractId],
        queryFn: () => signatureAPI.getAuditTrail(selectedContractId),
        enabled: !!selectedContractId // Always fetch when contract is selected
    });

    const signMutation = useMutation({
        mutationFn: (data: any) => signatureAPI.sign(data),
        onSuccess: () => {
            toast.success('Signature applied securely');
        },
        onError: (err) => {
            console.error(err);
            toast.error('Failed to sign contract');
        },
    });

    const clear = () => {
        sigCanvas.current?.clear();
        setTrimmedDataURL(null);
    }

    const save = () => {
        if (!sigCanvas.current) return;

        if (sigCanvas.current.isEmpty()) {
            toast.error('Please provide a signature first');
            return;
        }

        try {
            if (typeof sigCanvas.current.getCanvas !== 'function') {
                throw new Error('Canvas ref not initialized correctly');
            }

            // Use getCanvas() as getTrimmedCanvas has bundling issues with Vite
            const canvas = sigCanvas.current.getCanvas();
            const dataUrl = canvas.toDataURL('image/png');

            setTrimmedDataURL(dataUrl);

            signMutation.mutate({
                contract_id: selectedContractId,
                signer_name: signerName,
                signature_data: dataUrl
            });
        } catch (e: any) {
            console.error("Signature processing error:", e);
            toast.error(`Error: ${e.message || 'Unknown error'}`);
        }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <PenTool className="w-8 h-8 text-primary-600" />
                        E-Signature Module
                    </h1>
                    <p className="text-gray-500 mt-1">Legally binding digital signatures with audit trail</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Signing Area */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div className="mb-4 flex justify-between items-center">
                            <label className="block text-sm font-medium text-gray-700">Digital Signature Pad</label>
                            <button onClick={clear} className="text-sm text-gray-500 hover:text-red-600 flex items-center gap-1">
                                <Undo className="w-3 h-3" /> Clear
                            </button>
                        </div>

                        <div className="border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 overflow-hidden relative" style={{ height: 300 }}>
                            {!trimmedDataURL ? (
                                <SignatureCanvas
                                    ref={sigCanvas}
                                    penColor="black"
                                    canvasProps={{ className: 'w-full h-full cursor-crosshair' }}
                                    backgroundColor="rgba(255,255,255,0)"
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full">
                                    <img src={trimmedDataURL} alt="Signed" className="max-h-full" />
                                </div>
                            )}
                            {!trimmedDataURL && (
                                <div className="absolute bottom-2 right-2 text-xs text-gray-400 pointer-events-none select-none">
                                    Sign above
                                </div>
                            )}
                        </div>

                        <div className="mt-6 flex gap-4">
                            <button
                                onClick={save}
                                disabled={!!trimmedDataURL}
                                className="flex-1 bg-primary-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                            >
                                <PenTool className="w-4 h-4" />
                                {trimmedDataURL ? 'Signed' : 'Apply Signature'}
                            </button>
                        </div>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 flex gap-3 text-sm text-blue-800">
                        <ShieldCheck className="w-5 h-5 shrink-0" />
                        <div>
                            <p className="font-semibold">Secure & Binding</p>
                            <p className="opacity-90">This signature is cryptographically hashed and time-stamped in compliance with ESIGN and eIDAS regulations.</p>
                        </div>
                    </div>
                </div>

                {/* Info & Audit */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <FileText className="w-4 h-4" /> Contract Details
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-gray-500 font-medium uppercase">Contract ID</label>
                                <div className="font-mono text-sm">{selectedContractId}</div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 font-medium uppercase">Signer</label>
                                <div className="font-medium text-gray-900">{signerName}</div>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 font-medium uppercase">Date</label>
                                <div className="text-gray-900">{new Date().toLocaleDateString()}</div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <History className="w-4 h-4" /> Audit Trail
                        </h3>
                        <div className="space-y-4 relative pl-2">
                            {/* Timeline Line */}
                            <div className="absolute left-2.5 top-2 bottom-2 w-px bg-gray-200" />

                            {auditData?.data?.map((log: any) => (
                                <div key={log.id} className="relative pl-6">
                                    <div className="absolute left-0 top-1.5 w-5 h-5 bg-white border-2 border-primary-500 rounded-full z-10" />
                                    <p className="text-sm font-medium text-gray-900">{log.action.replace('_', ' ')}</p>
                                    <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>
                                    <p className="text-xs text-gray-400 mt-1">IP: {log.ip_address}</p>
                                </div>
                            ))}
                            {!auditData?.data && (
                                <p className="text-sm text-gray-400 text-center py-4">Status: Pending Signature</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
