const fs = require('fs');
const path = require('path');

const source = fs.readFileSync(
  path.join(__dirname, 'TabReglasMargen.jsx'),
  'utf8'
);

describe('TabReglasMargen margen sin hardcode', () => {
  test('no usa 30 como default funcional', () => {
    expect(source).not.toContain(
      'margen_esperado: 30,'
    );

    expect(source).not.toContain(
      'regla.margen_esperado || 30'
    );
  });

  test('nueva regla inicia sin margen inventado', () => {
    const matches =
      source.match(/margen_esperado:\s*null,/g) || [];

    expect(matches.length).toBeGreaterThanOrEqual(2);
  });

  test('edicion conserva margen existente', () => {
    expect(source).toContain(
      'margen_esperado: regla.margen_esperado ?? null,'
    );
  });

  test('submit exige margen explicito', () => {
    expect(source).toContain(
      "form.margen_esperado === null"
    );

    expect(source).toContain(
      "form.margen_esperado === undefined"
    );
  });
});
