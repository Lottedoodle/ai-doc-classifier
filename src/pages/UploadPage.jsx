import { useState, useEffect, useCallback } from 'react';
import DropZone from '../components/DropZone';
import DocumentCard from '../components/DocumentCard';
import { DOC_TYPES, DOC_TYPE_KEYS } from '../docTypes';
import * as api from '../api';

let queueId = 0;

export default function UploadPage() {
  const [documents, setDocuments] = useState([]);
  const [queue, setQueue] = useState([]); // ไฟล์ที่กำลังอัปโหลด/จำแนก
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const docs = await api.fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDrop = async (files) => {
    setError('');
    const items = files.map((file) => ({ id: ++queueId, name: file.name, file }));
    setQueue((prev) => [...prev, ...items]);

    // อัปโหลดทีละไฟล์ (ให้ AI classify เรียงลำดับ)
    for (const item of items) {
      try {
        const record = await api.uploadDocument(item.file);
        setDocuments((prev) => [record, ...prev]);
      } catch (err) {
        setError(`${item.name}: ${err.message}`);
      } finally {
        setQueue((prev) => prev.filter((q) => q.id !== item.id));
      }
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('ต้องการลบเอกสารนี้?')) return;
    try {
      await api.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleChangeType = async (id, docType) => {
    try {
      const updated = await api.updateDocumentType(id, docType);
      setDocuments((prev) => prev.map((d) => (d.id === id ? updated : d)));
    } catch (err) {
      setError(err.message);
    }
  };

  const counts = DOC_TYPE_KEYS.reduce((acc, key) => {
    acc[key] = documents.filter((d) => d.docType === key).length;
    return acc;
  }, {});

  const filtered = filter === 'all' ? documents : documents.filter((d) => d.docType === filter);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-brand-700 to-violet-700 bg-clip-text text-transparent">
          อัปโหลดเอกสาร ให้ AI จำแนกประเภท
        </h2>
        <p className="text-slate-500 mt-2">
          ระบบจะวิเคราะห์และจำแนกเอกสารเป็น 4 ประเภทโดยอัตโนมัติ —
          ใบสั่งซื้อ (PO) · ใบแจ้งหนี้ (Invoice) · ใบเสร็จรับเงิน (Receipt) · เอกสารทั่วไป
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-600 ml-3">✕</button>
        </div>
      )}

      <DropZone onDrop={handleDrop} />

      {/* กำลังประมวลผล */}
      {queue.length > 0 && (
        <div className="bg-white/80 backdrop-blur rounded-2xl border border-brand-200 p-4 space-y-2">
          {queue.map((item) => (
            <div key={item.id} className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin shrink-0" />
              <p className="text-sm text-slate-700 truncate flex-1">{item.name}</p>
              <span className="text-xs text-brand-600 font-medium animate-pulse">กำลังให้ AI จำแนกประเภท...</span>
            </div>
          ))}
        </div>
      )}

      {/* filter tabs */}
      {documents.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all ${
              filter === 'all'
                ? 'bg-slate-900 text-white shadow-md'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            ทั้งหมด ({documents.length})
          </button>
          {DOC_TYPE_KEYS.map((key) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all ${
                filter === key
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${DOC_TYPES[key].dot}`} />
              {DOC_TYPES[key].short} ({counts[key]})
            </button>
          ))}
        </div>
      )}

      {/* document grid */}
      {filtered.length === 0 ? (
        <div className="bg-white/60 rounded-3xl border border-dashed border-slate-300 p-16 text-center">
          <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-slate-500 font-medium">
            {documents.length === 0
              ? 'ยังไม่มีเอกสาร — ลากไฟล์มาวางด้านบนเพื่อเริ่มจำแนก'
              : 'ไม่มีเอกสารในประเภทนี้'}
          </p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((doc) => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onDelete={handleDelete}
              onChangeType={handleChangeType}
            />
          ))}
        </div>
      )}
    </div>
  );
}
