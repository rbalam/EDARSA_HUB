/**
 * Utilidades de exportación canónicas del Portal Inteligencia.
 * Excel (xlsx) y PDF (jspdf + autotable). Reutilizadas por TODAS las vistas.
 */
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const stamp = () => new Date().toISOString().slice(0, 16).replace('T', '_').replace(/:/g, '');

/**
 * Exporta una o varias hojas a un archivo .xlsx
 * @param {string} filename  Nombre base del archivo (sin extensión)
 * @param {Array<{name:string, columns:Array<{key:string,label:string}>, rows:Array<Object>}>} sheets
 */
export function exportToExcel(filename, sheets) {
  const wb = XLSX.utils.book_new();
  (sheets || []).forEach((s, i) => {
    const data = (s.rows || []).map((r) => {
      const o = {};
      (s.columns || []).forEach((c) => { o[c.label] = r[c.key]; });
      return o;
    });
    const ws = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(wb, ws, (s.name || `Hoja${i + 1}`).slice(0, 31));
  });
  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  saveAs(new Blob([buf], { type: 'application/octet-stream' }), `${filename}_${stamp()}.xlsx`);
}

/**
 * Exporta una tabla a PDF.
 * @param {string} title    Título del reporte
 * @param {Array<{key:string,label:string}>} columns
 * @param {Array<Object>} rows
 * @param {string} meta      Línea de metadatos (unidad/periodo)
 */
export function exportToPDF(title, columns, rows, meta = '') {
  const doc = new jsPDF({ orientation: (columns || []).length > 5 ? 'landscape' : 'portrait' });
  doc.setFontSize(14);
  doc.setTextColor(20);
  doc.text(title, 14, 16);
  let startY = 22;
  if (meta) {
    doc.setFontSize(9);
    doc.setTextColor(120);
    doc.text(meta, 14, 22);
    startY = 28;
  }
  autoTable(doc, {
    startY,
    head: [columns.map((c) => c.label)],
    body: (rows || []).map((r) => columns.map((c) => {
      const v = r[c.key];
      return v === null || v === undefined ? '' : v;
    })),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [16, 185, 129], textColor: 255 },
    alternateRowStyles: { fillColor: [245, 247, 250] },
    margin: { left: 14, right: 14 },
  });
  doc.save(`${title.replace(/\s+/g, '_')}_${stamp()}.pdf`);
}
