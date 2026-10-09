import {
  exportToExcel,
  exportToPDF,
  exportToTXT,
} from '../../portal-inteligencia/utils/exportUtils';

const columnsFromRows = (rows) => {
  const first = Array.isArray(rows) && rows.length ? rows[0] : {};
  return Object.keys(first || {}).slice(0, 32).map((key) => ({ key, label: key }));
};

export const resolveActionDataset = (action, viewData, systemDatasets = []) => {
  const payload = action?.payload || {};

  if (payload.dataset_id) {
    const dataset = (systemDatasets || []).find(
      (item) => item?.dataset_id === payload.dataset_id
    );
    if (!dataset) return null;
    const rows = Array.isArray(dataset.rows) ? dataset.rows : [];
    const columns = Array.isArray(dataset.columns) && dataset.columns.length
      ? dataset.columns.slice(0, 32).map((key) => ({ key, label: key }))
      : columnsFromRows(rows);
    return {
      rows,
      columns,
      title: payload.title || dataset.title || 'Análisis EDARSAHUB',
      meta: dataset.source_operation_id || 'EDARSAHUB',
    };
  }

  const datasetName = payload.dataset === 'lines' ? 'lines' : 'tickets';
  const rows = Array.isArray(viewData?.[datasetName]) ? viewData[datasetName] : [];
  return {
    rows,
    columns: columnsFromRows(rows),
    title: payload.title || 'Análisis EDARSAHUB',
    meta: 'Vista actual EDARSAHUB',
  };
};

export const exportActionDataset = (action, resolved) => {
  if (!resolved || !Array.isArray(resolved.rows)) return false;

  const payload = action?.payload || {};
  const filename = payload.filename || 'edarsahub_ia';
  const title = payload.title || resolved.title || 'Análisis EDARSAHUB';

  if (payload.format === 'xlsx') {
    exportToExcel(filename, [{
      name: title,
      columns: resolved.columns,
      rows: resolved.rows,
    }]);
    return true;
  }

  if (payload.format === 'pdf') {
    exportToPDF(title, resolved.columns, resolved.rows, resolved.meta || '');
    return true;
  }

  if (payload.format === 'txt') {
    exportToTXT(filename, resolved.columns, resolved.rows, resolved.meta || '');
    return true;
  }

  return false;
};
