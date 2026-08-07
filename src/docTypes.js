// การตั้งค่าประเภทเอกสารทั้ง 4 ประเภท (ตรงกับ backend classifier)
export const DOC_TYPES = {
  purchase_order: {
    label: 'ใบสั่งซื้อ (PO)',
    short: 'PO',
    badge: 'bg-violet-100 text-violet-700 border-violet-200',
    dot: 'bg-violet-500',
    bar: 'bg-violet-500',
    card: 'bg-violet-50 border-violet-200 text-violet-800',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  },
  invoice: {
    label: 'ใบแจ้งหนี้ (Invoice)',
    short: 'Invoice',
    badge: 'bg-amber-100 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    bar: 'bg-amber-500',
    card: 'bg-amber-50 border-amber-200 text-amber-800',
    icon: 'M9 7h6m-6 4h6m-6 4h4m-9 5V4a2 2 0 012-2h10a2 2 0 012 2v16l-3-2-2 2-2-2-2 2-2-2-3 2z',
  },
  receipt: {
    label: 'ใบเสร็จรับเงิน (Receipt)',
    short: 'Receipt',
    badge: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    bar: 'bg-emerald-500',
    card: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
  },
  general: {
    label: 'เอกสารทั่วไป',
    short: 'General',
    badge: 'bg-slate-100 text-slate-600 border-slate-200',
    dot: 'bg-slate-400',
    bar: 'bg-slate-400',
    card: 'bg-slate-50 border-slate-200 text-slate-700',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  },
};

export const DOC_TYPE_KEYS = Object.keys(DOC_TYPES);
