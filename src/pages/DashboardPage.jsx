import { useState, useEffect } from 'react';
import { DOC_TYPES, DOC_TYPE_KEYS } from '../docTypes';
import * as api from '../api';

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatCard({ typeKey, count, total }) {
  const cfg = DOC_TYPES[typeKey];
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className={`rounded-2xl p-5 border shadow-sm ${cfg.card}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="w-9 h-9 rounded-xl bg-white/70 flex items-center justify-center">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d={cfg.icon} />
          </svg>
        </div>
        <span className="text-xs font-medium opacity-70">{pct}%</span>
      </div>
      <p className="text-3xl font-bold tabular-nums">{count}</p>
      <p className="text-sm mt-1 opacity-80">{cfg.label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const [documents, setDocuments] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.fetchDocuments().then((docs) => {
      setDocuments(docs);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const counts = DOC_TYPE_KEYS.reduce((acc, key) => {
    acc[key] = documents.filter((d) => d.docType === key).length;
    return acc;
  }, {});
  const total = documents.length;
  const aiCount = documents.filter((d) => d.method === 'ai').length;

  const filtered = filter === 'all' ? documents : documents.filter((d) => d.docType === filter);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
        <p className="text-slate-500 mt-1">สรุปผลการจำแนกเอกสารทั้งหมด {total} ฉบับ</p>
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {DOC_TYPE_KEYS.map((key) => (
          <StatCard key={key} typeKey={key} count={counts[key]} total={total} />
        ))}
      </div>

      {/* distribution bar */}
      {total > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-700">สัดส่วนประเภทเอกสาร</span>
            <span className="text-xs text-slate-400">
              จำแนกด้วย AI {aiCount}/{total} ฉบับ
            </span>
          </div>
          <div className="h-3 bg-slate-100 rounded-full overflow-hidden flex">
            {DOC_TYPE_KEYS.map((key) => (
              counts[key] > 0 && (
                <div
                  key={key}
                  className={`${DOC_TYPES[key].bar} h-full transition-all duration-500`}
                  style={{ width: `${(counts[key] / total) * 100}%` }}
                  title={`${DOC_TYPES[key].label}: ${counts[key]}`}
                />
              )
            ))}
          </div>
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500">
            {DOC_TYPE_KEYS.map((key) => (
              <span key={key} className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${DOC_TYPES[key].dot}`} />
                {DOC_TYPES[key].short} ({counts[key]})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all ${
            filter === 'all'
              ? 'bg-slate-900 text-white shadow-md'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          ทั้งหมด
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
            {DOC_TYPES[key].short}
          </button>
        ))}
      </div>

      {/* table */}
      {filtered.length === 0 ? (
        <div className="bg-white/60 rounded-3xl border border-dashed border-slate-300 p-16 text-center">
          <p className="text-slate-500">
            {documents.length === 0
              ? 'ยังไม่มีเอกสาร — ไปที่หน้า "อัปโหลด & จำแนก" เพื่อเริ่มต้น'
              : 'ไม่มีเอกสารในประเภทนี้'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">เอกสาร</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">ประเภท</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">ความมั่นใจ</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">วิธีจำแนก</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">เหตุผล</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">ไฟล์</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((doc) => {
                  const cfg = DOC_TYPES[doc.docType] || DOC_TYPES.general;
                  const pct = Math.round((doc.confidence || 0) * 100);
                  return (
                    <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-4">
                        <p className="font-medium text-slate-800 truncate max-w-[220px]" title={doc.originalName}>
                          {doc.originalName}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {formatSize(doc.size)} · {new Date(doc.uploadedAt).toLocaleDateString('th-TH')}
                        </p>
                      </td>
                      <td className="px-5 py-4">
                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${cfg.badge}`}>
                          <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2 justify-center">
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className={`h-full ${cfg.bar}`} style={{ width: `${pct}%` }} />
                          </div>
                          <span className="text-xs text-slate-500 tabular-nums w-9">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                          doc.method === 'ai'
                            ? 'bg-brand-100 text-brand-700'
                            : doc.method === 'manual'
                              ? 'bg-slate-200 text-slate-700'
                              : 'bg-amber-100 text-amber-700'
                        }`}>
                          {doc.method === 'ai' ? 'AI' : doc.method === 'manual' ? 'Manual' : 'Keyword'}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <p className="text-xs text-slate-500 max-w-[240px] truncate" title={doc.reason}>
                          {doc.reason || '—'}
                        </p>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <a
                          href={`/uploads/${doc.storedName}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 transition-colors"
                        >
                          เปิดดู
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
