// backend/modules/edge/comandero_terminal_ui.ts

import { 
    TicketFinanciero, 
    ProductoUniversal, 
    UnidadNegocio 
} from "../contract/edarsa_contracts";

export interface MesaEstadoUI {
    id_mesa: string;
    estado: 'VERDE' | 'AMARILLO' | 'ROJO';
    minutos_inactividad: number;
    tipo_comensal: 'PUBLICO' | 'SOCIO_CAVA' | 'INVERSIONISTA' | 'PERSONAL' | null;
}

export class ComanderoAlphaTerminalUI {
    private dispositivoId: string = "POS-MOBILE-EDGE-01";
    private mesaSeleccionada: MesaEstadoUI | null = null;
    private itemsComandaActual: Array<{ id_producto: string; cantidad: number; precio_unitario: number }> = [];

    constructor() {}

    // ============================================================================
    // 3.1. MAPA DE MESAS LIVE 3D: CICLO DE EVENTOS REACTIVO (IdleTimeEvent)
    // ============================================================================
    /**
     * Calcula de forma autónoma el estado de alerta cromática de cada mesa en la tablet
     * basándose estrictamente en los minutos transcurridos desde la última interacción.
     */
    public calcularAlertaCromaticaMesa(mesa: MesaEstadoUI): 'VERDE' | 'AMARILLO' | 'ROJO' {
        if (mesa.estado === 'AMARILLO') {
            return 'AMARILLO'; // Cuenta solicitada, activa división Drag-and-Drop de inmediato [cite: 258, 259]
        }
        
        if (mesa.minutos_inactividad >= 12) {
            return 'ROJO'; // Alerta crítica de abandono: Inyecta script push al vendedor [cite: 184, 260]
        }
        
        return 'VERDE'; // Flujo de consumo activo y estable en el salón [cite: 182, 257]
    }

    // ============================================================================
    // 3.2. REGLA DE LOS 3 TOQUES: CONMUTACIÓN DE SEGMENTO Y APERTURA (TOQUE 1)
    // ============================================================================
    /**
     * TOQUE 1: Selecciona la mesa en el plano físico e inyecta el tipo de comensal
     * para reajustar las listas de precios en background sin duplicar tablas.
     */
    public uiToque1AbrirMesa(mesa: MesaEstadoUI, tipo: 'PUBLICO' | 'SOCIO_CAVA' | 'INVERSIONISTA' | 'PERSONAL'): void {
        this.mesaSeleccionada = {
            ...mesa,
            tipo_comensal: tipo
        };
        this.itemsComandaActual = [];
        console.log(`[UI MASTER]: Mesa ${mesa.id_mesa} abierta. Modo: ${tipo}. Cuentas aisladas asignadas.`);
    }

    // ============================================================================
    // 3.3. BOTONERA PROPORCIONAL 60/40 E INYECCIÓN IA (TOQUE 2)
    // ============================================================================
    /**
     * TOQUE 2: Captura un elemento de la cuadrícula adaptativa (60% Predictivo / 40% Lateral Push).
     * Intercepta el evento localmente para sugerir el maridaje ínclito de mayor margen.
     */
    public uiToque2SeleccionarProducto(
        producto: ProductoUniversal, 
        motorReglasBackend: any
    ): { detonar_popup_maridaje: boolean; script_sugerido: string } {
        
        // Agregar el ítem al buffer visual en milisegundos
        this.itemsComandaActual.push({
            id_producto: producto.id_producto,
            cantidad: 1,
            precio_unitario: producto.precio_final
        });

        // Interrogación directa al cerebro local (Paso 2) para venta sugestiva cruzada [cite: 551]
        const maridajeSugerido = motorReglasBackend.interceptar_producto_para_maridaje(producto.id_producto);
        
        if (maridajeSugerido) {
            return {
                detonar_popup_maridaje: true,
                script_sugerido: maridajeSugerido.argumento_pantalla
            };
        }

        return { detonar_popup_maridaje: false, script_sugerido: "" };
    }

    // ============================================================================
    // 3.4. DESPACHO INMUTABLE Y CIERRE ASERTIVO (TOQUE 3)
    // ============================================================================
    /**
     * TOQUE 3: Confirma y envía la comanda al disco duro local.
     * Genera el payload universal inmutable desacoplado de internet.
     */
    public uiToque3MandarComanda(comanderoLocalCore: any, empleadoId: string): string {
        if (!this.mesaSeleccionada) throw new Error("No hay ninguna mesa activa seleccionada en la tablet.");

        const subtotal = this.itemsComandaActual.reduce((acc, item) => acc + (item.precio_unitario * item.cantidad), 0);
        
        // Cálculo paramétrico de impuestos y totales financieros locales
        const totales = {
            subtotal_neto: Number((subtotal / 1.16).toFixed(2)),
            total_iva: Number((subtotal - (subtotal / 1.16)).toFixed(2)),
            propina_sugerida: Number((subtotal * 0.15).toFixed(2)),
            gran_total: subtotal
        };

        const contabilidadDefault = {
            cuenta_ingresos: this.mesaSeleccionada.tipo_comensal === 'PUBLICO' ? "401.01_ventas_alimentos" : "601.08_costo_personal",
            cuenta_impuestos: "219.01_iva_trasladado",
            cuenta_caja_bancos: "102.02_terminal_bancaria_visa"
        };

        // Inyección física directa en el almacenamiento inmutable (Paso 1)
        const uuidGlobalIdempotente = comanderoLocalCore.registrar_comanda_offline(
            this.mesaSeleccionada.id_mesa,
            empleadoId,
            this.mesaSeleccionada.tipo_comensal,
            this.itemsComandaActual,
            totales,
            contabilidadDefault
        );

        // Liberación inmediata de la pantalla para el vendedor
        this.itemsComandaActual = [];
        this.mesaSeleccionada = null;
        
        console.log(`[UI SYSTEM]: Comanda despachada con éxito. Transacción guardada en cola FIFO local.`);
        return uuidGlobalIdempotente;
    }
}
