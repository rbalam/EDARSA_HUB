export const IA_CHART_PALETTE = Object.freeze([
  '#4F46E5',
  '#06B6D4',
  '#22C55E',
  '#F59E0B',
  '#EF4444',
  '#8B5CF6',
  '#EC4899',
  '#14B8A6',
  '#84CC16',
  '#F97316',
]);

export const iaChartColor = (index = 0) => {
  const numeric = Number.isFinite(Number(index)) ? Number(index) : 0;
  const normalized = ((numeric % IA_CHART_PALETTE.length) + IA_CHART_PALETTE.length)
    % IA_CHART_PALETTE.length;
  return IA_CHART_PALETTE[normalized];
};
