
import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { driveAPI } from '../services/api';
import {
    Folder,
    FileText,
    Search,
    Upload,
    Plus,
    Trash2,
    HardDrive,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function DocumentDrive() {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [currentFolder, setCurrentFolder] = useState<any>(null); // null = root

    const { data: filesData, isLoading } = useQuery({
        queryKey: ['drive-files', currentFolder?.id],
        queryFn: () => driveAPI.listFiles(currentFolder?.id),
    });

    const files = filesData?.data || [];

    const createFolderMutation = useMutation({
        mutationFn: (name: string) => driveAPI.createFolder(name, currentFolder?.id),
        onSuccess: () => {
            toast.success('Folder created');
            queryClient.invalidateQueries({ queryKey: ['drive-files'] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => driveAPI.deleteItem(id),
        onSuccess: () => {
            toast.success('Item deleted');
            queryClient.invalidateQueries({ queryKey: ['drive-files'] });
        },
    });

    const uploadMutation = useMutation({
        mutationFn: (file: File) => driveAPI.uploadFile(file, currentFolder?.id),
        onSuccess: () => {
            toast.success('File uploaded');
            queryClient.invalidateQueries({ queryKey: ['drive-files'] });
            if (fileInputRef.current) fileInputRef.current.value = '';
        },
        onError: () => toast.error('Upload failed'),
    });

    const handleCreateFolder = () => {
        const name = prompt('Folder name:');
        if (name) createFolderMutation.mutate(name);
    };

    const handleFileClick = (file: any) => {
        if (file.type === 'folder') {
            setCurrentFolder(file);
        } else {
            toast('File preview not available', { icon: '📄' });
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            uploadMutation.mutate(file);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-64px)] flex flex-col">
            {/* Hidden File Input */}
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
            />

            {/* Header */}
            <div className="flex justify-between items-center mb-6 shrink-0">
                <div className="flex items-center gap-3">
                    <HardDrive className="w-8 h-8 text-primary-600" />
                    <h1 className="text-3xl font-bold text-gray-900">Document Drive</h1>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search files..."
                            className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 w-64"
                        />
                    </div>
                    <button onClick={handleCreateFolder} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                        <Plus className="w-4 h-4" /> New Folder
                    </button>
                    <button
                        onClick={handleUploadClick}
                        disabled={uploadMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm disabled:opacity-50"
                    >
                        <Upload className="w-4 h-4" />
                        {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                    </button>
                </div>
            </div>

            {/* Breadcrumbs */}
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-6 shrink-0">
                <button
                    onClick={() => setCurrentFolder(null)}
                    className={`hover:text-primary-600 ${!currentFolder ? 'font-semibold text-gray-900' : ''}`}
                >
                    My Drive
                </button>
                {currentFolder && (
                    <>
                        <span>/</span>
                        <span className="font-semibold text-gray-900">{currentFolder.name}</span>
                    </>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
                {isLoading ? (
                    <div className="flex-1 flex items-center justify-center text-gray-400">Loading...</div>
                ) : files.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                        <Folder className="w-16 h-16 mb-4 opacity-20" />
                        <p>Empty folder</p>
                    </div>
                ) : (
                    <div className="p-4 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {files.map((file: any) => (
                            <div
                                key={file.id}
                                onClick={() => handleFileClick(file)}
                                className="group relative p-4 rounded-xl border border-gray-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all cursor-pointer flex flex-col gap-3"
                            >
                                <div className="flex justify-between items-start">
                                    <div className={`p-3 rounded-lg ${file.type === 'folder' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'}`}>
                                        {file.type === 'folder' ? <Folder className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(file.id); }}
                                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-lg transition-all"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-900 truncate" title={file.name}>{file.name}</h3>
                                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                                        {file.type === 'folder' ? 'Folder' : file.size} • {new Date(file.modified_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
