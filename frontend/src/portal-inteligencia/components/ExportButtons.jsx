/**
 * Botones de exportación canónicos (Excel + PDF) reutilizables.
 */
import React from 'react';
import { FileSpreadsheet, FileText } from 'lucide-react';
import { exportToExcel, exportToPDF } from '../utils/exportUtils';

export function ExportButtons({ filename, title, columns, rows, meta = '', sheets = null, testid = 'export' }) {
  const disabled = (!rows || rows.length === 0) && (!sheets || sheets.length === 0);
  const handleExcel = () => {
    if (sheets) exportToExcel(filename, sheets);
    else exportToExcel(filename, [{ name: title, columns, rows }]);
  };
  const handlePDF = () => exportToPDF(title, columns, rows, meta);
  return (
    <div className="flex gap-2">
      <button
        onClick={handleExcel}
        disabled={disabled}
        data-testid={`${testid}-excel-btn`}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600/90 hover:bg-emerald-600 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <FileSpreadsheet className="h-3.5 w-3.5" /> Excel
      </button>
      <button
        onClick={handlePDF}
        disabled={disabled}
        data-testid={`${testid}-pdf-btn`}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-600/90 hover:bg-rose-600 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <FileText className="h-3.5 w-3.5" /> PDF
      </button>
    </div>
  );
}
