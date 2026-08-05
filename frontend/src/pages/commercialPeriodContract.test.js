import {
  aplicarContratoPeriodo,
  normalizarModoContratoPeriodo,
} from './commercialPeriodContract';


describe('contrato canonico historico', () => {
  test('aplica proyeccion y comparativos del backend', () => {
    const responseData = {
      totales: {
        ventas: 1465947.63,
        pax_promedio: null,
        cheque_promedio: null,
        ticket_promedio: null,
        proyeccion: null,
        var_vs_mes_ant: null,
        var_vs_año_ant: null,
      },
      periodo: {
        modo_historico_explicito: true,
        fecha_inicio: '2026-08-01',
        fecha_fin: '2026-08-03',
      },
      unidades: [{
        unidad_negocio_codigo: '130MID',
        ventas: 300000,
        pax_promedio: null,
        cheque_promedio: null,
        ticket_promedio: null,
        proyeccion: null,
        var_vs_mes_ant: null,
        var_vs_año_ant: null,
      }],
    };

    const contratoGeneral = {
      actual: {
        pax_promedio: 1465.94763,
        cheque_promedio: 2931.89526,
      },
      comparativos: {
        inmediato: {
          var_ventas: 10.5,
          var_pax: 4.5,
          var_cheques: 3.5,
          var_proyeccion: 8.5,
          ventas: 1320000,
          pax: 950,
          cheques: 480,
        },
        anual: {
          var_ventas: 20.5,
          var_pax: 14.5,
          var_cheques: 13.5,
          var_proyeccion: 18.5,
          ventas: 1210000,
          pax: 900,
          cheques: 450,
        },
      },
      proyeccion: {
        proyeccion_total: 15100000,
        metodo: 'CANONICO_BACKEND',
        nivel_confianza: 'ALTA',
        detalle: [],
      },
      unidades_con_datos: {
        actual: 5,
        periodo_anterior: 5,
        anio_anterior: 5,
      },
      modo_periodo: 'historico',
      periodos: {
        fecha_corte_datos: '2026-08-03',
        periodo_cerrado: true,
      },
      etiquetas: {
        actual: 'Agosto 2026',
      },
    };

    const contratosUnidad = {
      '130MID': {
        actual: {
          pax_promedio: 1200,
          cheque_promedio: 2400,
        },
        comparativos: {
          inmediato: {
            var_ventas: 11,
            var_pax: 6,
            var_cheques: 5,
            var_proyeccion: 9,
            ventas: 270000,
            pax: 240,
            cheques: 120,
          },
          anual: {
            var_ventas: 21,
            var_pax: 16,
            var_cheques: 15,
            var_proyeccion: 19,
            ventas: 250000,
            pax: 220,
            cheques: 110,
          },
        },
        proyeccion: {
          proyeccion_total: 3100000,
          metodo: 'CANONICO_UNIDAD',
          nivel_confianza: 'MEDIA',
          detalle: [],
        },
      },
    };

    const result = aplicarContratoPeriodo(
      responseData,
      contratoGeneral,
      contratosUnidad,
    );

    expect(result.totales.ventas).toBe(1465947.63);
    expect(result.totales.proyeccion).toBe(15100000);
    expect(result.totales.var_vs_mes_ant).toBe(10.5);
    expect(result.totales.var_vs_año_ant).toBe(20.5);
    expect(result.totales.pax_promedio).toBe(1465.94763);
    expect(result.totales.cheque_promedio).toBe(2931.89526);
    expect(result.totales.ticket_promedio).toBe(2931.89526);
    expect(result.totales.proyeccion_metodo)
      .toBe('CANONICO_BACKEND');
    expect(result.totales.proyeccion_confianza)
      .toBe('ALTA');

    expect(result.unidades[0].ventas).toBe(300000);
    expect(result.unidades[0].proyeccion).toBe(3100000);
    expect(result.unidades[0].var_vs_mes_ant).toBe(11);
    expect(result.unidades[0].var_vs_año_ant).toBe(21);
    expect(result.unidades[0].pax_promedio).toBe(1200);
    expect(result.unidades[0].cheque_promedio).toBe(2400);
    expect(result.unidades[0].ticket_promedio).toBe(2400);
    expect(result.unidades[0].proyeccion_metodo)
      .toBe('CANONICO_UNIDAD');

    expect(result.periodo.modo_historico_explicito)
      .toBe(true);
    expect(result.periodo.modo_periodo).toBe('historico');
    expect(result.periodo.fecha_corte_datos)
      .toBe('2026-08-03');
    expect(result._contrato_periodo)
      .toBe(contratoGeneral);
  });
});


describe('normalizacion del modo del contrato comercial', () => {
  test('traduce historico al enum mensual del backend', () => {
    expect(
      normalizarModoContratoPeriodo('historico'),
    ).toBe('mensual');
  });

  test('conserva ventas_dia', () => {
    expect(
      normalizarModoContratoPeriodo('ventas_dia'),
    ).toBe('ventas_dia');
  });

  test('conserva mensual', () => {
    expect(
      normalizarModoContratoPeriodo('mensual'),
    ).toBe('mensual');
  });

  test('rechaza modos no soportados', () => {
    expect(() => {
      normalizarModoContratoPeriodo('otro');
    }).toThrow(
      'Modo de contrato comercial no soportado: otro',
    );
  });
});
