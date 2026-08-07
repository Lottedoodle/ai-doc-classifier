import { useState } from 'react';
import { DOC_TYPES, DOC_TYPE_KEYS } from '../docTypes';

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function DocumentCard({ doc, onDelete, onChangeType }) {
  const [changing, setChanging] = useState(false);
  const cfg = DOC_TYPES[doc.docType] || DOC_TYPES.general;
  const isImage = doc.mimeType?.startsWith('image/');
  const url = `/uploads/${doc.storedName}`;
  const confidencePct = Math.round((doc.confidence || 0) * 100);

  const handleTypeChange = async (e) => {
    const next = e.target.value;
    if (next === doc.docType) return;
    setChanging(true);
    try {
      await onChangeType(doc.id, next);
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col">
      {/* preview */}
      <div className="h-36 bg-slate-100 relative flex items-center justify-center overflow-hidden">
        {isImage ? (
          <img src={url} alt={doc.originalName} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="text-center">
            <svg className="w-12 h-12 text-red-400 mx-auto" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM8 12h8v2H8v-2zm0 4h5v2H8v-2z" />
            </svg>
            <span className="text-xs text-slate-500">PDF</span>
          </div>
        )}
        <span className={`absolute top-2 left-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border shadow-sm backdrop-blur-sm ${cfg.badge}`}>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={cfg.icon} />
          </svg>
          {cfg.short}
        </span>
        {doc.method === 'ai' && (
          <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-brand-600/90 text-white font-medium shadow-sm">
            AI
          </span>
        )}
        {doc.method === 'manual' && (
          <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-slate-700/90 text-white font-medium shadow-sm">
            Manual
          </span>
        )}
      </div>

      {/* body */}
      <div className="p-4 flex-1 flex flex-col gap-2.5">
        <div>
          <p className="text-sm font-semibold text-slate-800 truncate" title={doc.originalName}>
            {doc.originalName}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {formatSize(doc.size)} · {formatDate(doc.uploadedAt)}
          </p>
        </div>

        {/* confidence */}
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
            <span>ความมั่นใจ</span>
            <span className="font-semibold tabular-nums">{confidencePct}%</span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${cfg.bar}`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        {doc.reason && (
          <p className="text-xs text-slate-500 bg-slate-50 rounded-lg px-2.5 py-1.5 line-clamp-2" title={doc.reason}>
            {doc.reason}
          </p>
        )}

        <div className="mt-auto space-y-2">
          <select
            value={doc.docType}
            onChange={handleTypeChange}
            disabled={changing}
            className="w-full text-xs px-2.5 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50 cursor-pointer"
            title="เปลี่ยนประเภทเอกสาร"
          >
            {DOC_TYPE_KEYS.map((key) => (
              <option key={key} value={key}>{DOC_TYPES[key].label}</option>
            ))}
          </select>

          <div className="flex gap-2">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center text-xs py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors font-medium"
            >
              เปิดดู
            </a>
            <button
              type="button"
              onClick={() => onDelete(doc.id)}
              className="flex-1 text-xs py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors font-medium"
            >
              ลบ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
