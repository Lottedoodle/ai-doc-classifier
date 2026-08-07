import { useState, useRef, useCallback } from 'react';

export default function DropZone({ onDrop, disabled }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    if (e.type === 'dragenter' || e.type === 'dragover') setDragging(true);
    else if (e.type === 'dragleave') setDragging(false);
  }, [disabled]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) onDrop(files);
  }, [onDrop, disabled]);

  const handleChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) onDrop(files);
    e.target.value = '';
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`relative overflow-hidden border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all duration-300 group ${
        dragging
          ? 'border-brand-500 bg-brand-50/80 scale-[1.01] shadow-xl shadow-brand-500/10'
          : 'border-slate-300 bg-white/70 hover:border-brand-400 hover:bg-brand-50/40 hover:shadow-lg'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*,.pdf"
        multiple
        onChange={handleChange}
        className="hidden"
        disabled={disabled}
      />

      <div className={`mx-auto w-20 h-20 rounded-3xl bg-gradient-to-br from-brand-500 to-violet-600 flex items-center justify-center mb-5 shadow-lg shadow-brand-500/30 transition-transform duration-300 ${dragging ? 'scale-110 rotate-3' : 'group-hover:scale-105'}`}>
        <svg className="w-9 h-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>

      <p className="text-lg font-bold text-slate-800 mb-1">
        {dragging ? 'วางไฟล์ได้เลย!' : 'ลากไฟล์มาวางที่นี่'}
      </p>
      <p className="text-sm text-slate-500 mb-4">หรือคลิกเพื่อเลือกไฟล์ — อัปโหลดได้ครั้งละหลายไฟล์</p>

      <div className="inline-flex items-center gap-2 text-xs text-slate-400 bg-slate-100/80 px-3 py-1.5 rounded-full">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        รองรับ JPG, PNG, GIF, WEBP, PDF · สูงสุด 10MB ต่อไฟล์
      </div>
    </div>
  );
}
