'use client';

import React, { useState, useRef } from 'react';
import { useUploadAsset } from '@/lib/api';
import { useSearchStore } from '@/store/useSearchStore';
import { 
  Upload, 
  FileText, 
  Video, 
  Volume2, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Trash2,
  AlertTriangle
} from 'lucide-react';

interface FileQueueItem {
  id: string;
  file: File;
  progress: number;
  status: 'Pending' | 'Uploading' | 'Completed' | 'Failed';
  errorMsg?: string;
  assetId?: string;
}

export default function UploadPage() {
  const [queue, setQueue] = useState<FileQueueItem[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadAssetMutation = useUploadAsset();
  const addRecentAsset = useSearchStore((state) => state.addRecentAsset);
  const updateRecentAssetStatus = useSearchStore((state) => state.updateRecentAssetStatus);

  const SUPPORTED_TYPES = [
    'text/plain',
    'application/pdf',
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'video/mp4',
    'video/quicktime' // .mov
  ];

  const getModalityIcon = (type: string) => {
    if (type.startsWith('text/') || type.includes('pdf')) {
      return <FileText className="w-5 h-5 text-blue-500" />;
    }
    if (type.startsWith('audio/')) {
      return <Volume2 className="w-5 h-5 text-amber-500" />;
    }
    if (type.startsWith('video/')) {
      return <Video className="w-5 h-5 text-purple-500" />;
    }
    return <FileText className="w-5 h-5 text-muted-foreground" />;
  };

  const validateFile = (file: File): string | null => {
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowedExts = ['.txt', '.pdf', '.mp3', '.wav', '.mp4', '.mov'];
    
    if (!allowedExts.includes(fileExt) && !SUPPORTED_TYPES.includes(file.type)) {
      return `Invalid format. Allowed: TXT, PDF, MP3, WAV, MP4, MOV`;
    }
    
    // 50MB file size limit for host speed
    if (file.size > 50 * 1024 * 1024) {
      return `File exceeds 50MB limit.`;
    }
    
    return null;
  };

  const handleFilesAdded = (filesList: FileList) => {
    const newItems: FileQueueItem[] = [];
    for (let i = 0; i < filesList.length; i++) {
      const file = filesList[i];
      const errorMsg = validateFile(file);
      
      newItems.push({
        id: Math.random().toString(36).substring(7),
        file,
        progress: 0,
        status: errorMsg ? 'Failed' : 'Pending',
        errorMsg: errorMsg || undefined
      });
    }
    setQueue((prev) => [...newItems, ...prev]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const removeItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const processUpload = async (item: FileQueueItem) => {
    // Mark as uploading
    setQueue((prev) =>
      prev.map((q) => (q.id === item.id ? { ...q, status: 'Uploading', progress: 30 } : q))
    );

    // Seed Zustand for dashboard updates
    const initialAsset = {
      id: item.id,
      name: item.file.name,
      status: 'Processing',
      timestamp: new Date().toISOString()
    };
    addRecentAsset(initialAsset);

    try {
      // Execute upload payload
      const response = await uploadAssetMutation.mutateAsync(item.file);
      
      // Mark as completed
      setQueue((prev) =>
        prev.map((q) =>
          q.id === item.id
            ? { ...q, status: 'Completed', progress: 100, assetId: response.asset_id }
            : q
        )
      );

      // Update Zustand details with backend asset metadata
      updateRecentAssetStatus(initialAsset.id, 'Completed', response.chunk_count);
    } catch (err: any) {
      // Mark as failed
      setQueue((prev) =>
        prev.map((q) =>
          q.id === item.id
            ? { ...q, status: 'Failed', progress: 0, errorMsg: err.message }
            : q
        )
      );

      updateRecentAssetStatus(initialAsset.id, 'Failed');
    }
  };

  const uploadAllPending = () => {
    queue.filter((q) => q.status === 'Pending').forEach((q) => processUpload(q));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="border-b border-border pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight">Upload Center</h1>
        <p className="text-muted-foreground mt-1">
          Ingest multi-modal raw content into semantic partition blocks and model index embeddings.
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        className={`
          flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200 text-center bg-card
          ${isDragActive 
            ? 'border-primary bg-primary/5 scale-[0.99]' 
            : 'border-border hover:border-muted-foreground/30'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          multiple
          onChange={(e) => e.target.files && handleFilesAdded(e.target.files)}
        />
        <div className="p-4 bg-secondary rounded-full text-muted-foreground mb-4">
          <Upload className="w-8 h-8" />
        </div>
        <h3 className="font-bold text-lg">Drag & Drop files here</h3>
        <p className="text-sm text-muted-foreground mt-1">
          or click to browse local folders
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-4 text-xs font-semibold text-muted-foreground bg-secondary/50 px-4 py-2 rounded-lg">
          <span>TXT</span>•<span>PDF</span>•<span>MP3</span>•<span>WAV</span>•<span>MP4</span>•<span>MOV</span>
        </div>
        <p className="text-[10px] text-muted-foreground/80 mt-2">
          Max file size: 50MB
        </p>
      </div>

      {/* Queue Controller Buttons */}
      {queue.some((q) => q.status === 'Pending') && (
        <div className="flex justify-end">
          <button
            onClick={uploadAllPending}
            className="px-5 py-2.5 bg-primary text-primary-foreground font-semibold text-sm rounded-md shadow-sm hover:bg-primary/90 transition"
          >
            Upload All Pending ({queue.filter((q) => q.status === 'Pending').length})
          </button>
        </div>
      )}

      {/* Upload Queue list */}
      {queue.length > 0 && (
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden divide-y divide-border">
          <div className="px-6 py-4 bg-secondary/50 font-bold text-sm text-muted-foreground flex items-center justify-between">
            <span>Upload Queue ({queue.length})</span>
            {queue.some((q) => q.status !== 'Uploading') && (
              <button 
                onClick={() => setQueue([])}
                className="text-xs text-destructive hover:underline flex items-center gap-1"
              >
                Clear Queue
              </button>
            )}
          </div>
          <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
            {queue.map((item) => (
              <div key={item.id} className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="p-2.5 bg-secondary rounded-lg shrink-0">
                    {getModalityIcon(item.file.type || item.file.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-sm text-foreground truncate">{item.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(item.file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                    
                    {/* Status & Error Display */}
                    {item.status === 'Failed' && item.errorMsg && (
                      <p className="text-xs text-destructive flex items-center gap-1 mt-1">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {item.errorMsg}
                      </p>
                    )}
                    
                    {item.status === 'Uploading' && (
                      <div className="w-full bg-secondary h-1.5 rounded-full mt-2 overflow-hidden">
                        <div 
                          className="bg-primary h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${item.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                  {/* Status Badges */}
                  {item.status === 'Pending' && (
                    <button
                      onClick={() => processUpload(item)}
                      className="px-3 py-1.5 bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold rounded-md border border-border transition"
                    >
                      Process Upload
                    </button>
                  )}

                  {item.status === 'Uploading' && (
                    <span className="flex items-center gap-1.5 text-xs text-amber-500 font-semibold bg-amber-500/10 px-2.5 py-1 rounded-full">
                      <Loader2 className="w-3 h-3 animate-spin" /> Ingesting...
                    </span>
                  )}

                  {item.status === 'Completed' && (
                    <span className="flex items-center gap-1.5 text-xs text-emerald-500 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full">
                      <CheckCircle className="w-3 h-3" /> Indexed
                    </span>
                  )}

                  {item.status === 'Failed' && (
                    <span className="flex items-center gap-1.5 text-xs text-red-500 font-semibold bg-red-500/10 px-2.5 py-1 rounded-full">
                      <AlertTriangle className="w-3 h-3" /> Failed
                    </span>
                  )}

                  {/* Trash Action */}
                  {item.status !== 'Uploading' && (
                    <button
                      onClick={() => removeItem(item.id)}
                      className="p-2 text-muted-foreground hover:text-destructive hover:bg-secondary rounded-lg transition"
                      title="Remove from queue"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
