// frontend/components/mapa_mesas_live3d.ts

import { MesaEstadoUI } from "../../backend/modules/edge/comandero_terminal_ui";
import { MotorInventarioParametrico } from "../../backend/modules/edge/motor_inventario_parametrico";

export class MapaMesasLive3D {
    private contenedorPiso: HTMLElement;
    private motorInventario: MotorInventarioParametrico;

    constructor(idContenedor: string) {
        this.contenedorPiso = document.getElementById(idContenedor) as HTMLElement;
        this.motorInventario = new MotorInventarioParametrico();
    }

    // ============================================================================
    // 3.1. RENDERIZADO DEL LIENZO DEL PISO DE VENTAS (ZONAS REALES)
    // ============================================================================
    /**
     * Dibuja de forma reactiva el mapa físico del salón en la tablet.
     * Asigna a cada mesa un detector cíclico de eventos de inactividad.
     */
    public inicializarPlanoSalon(listaMesas: MesaEstadoUI[]): void {
        this.contenedorPiso.innerHTML = ""; // Limpieza de búfer de renderizado

        listaMesas.forEach(mesa => {
            const elementoMesa = document.createElement("div");
            elementoMesa.id = `mesa-node-${mesa.id_mesa}`;
            elementoMesa.classList.add("mesa-contenedor-3d");
            
            // Determinar la alerta cromática en frío sin llamadas a internet
            const claseColor = this.obtenerClaseCromatica(mesa.minutos_inactividad, mesa.estado);
            elementoMesa.classList.add(claseColor);

            // Inyección de estructura HTML responsiva
            elementoMesa.innerHTML = `
                <div class="mesa-header">Mesa ${mesa.id_mesa}</div>
                <div class="mesa-body">
                    <span class="pax-tag">${mesa.tipo_comensal ? `👥 ${mesa.tipo_comensal}` : "Vacía"}</span>
                    <span class="timer-tag">${mesa.minutos_inactividad} min</span>
                </div>
            `;

            // TOQUE 1: Evento de apertura con selector elástico de segmento
            elementoMesa.addEventListener("click", () => this.detonarSelectorSegmento(mesa));
            
            this.contenedorPiso.appendChild(elementoMesa);
        });
    }

    private obtenerClaseCromatica(minutos: number, estado: string): string {
        if (estado === 'AMARILLO') return "color-amarillo-cierre"; // Cuenta solicitada (Drag-and-Drop)
        if (minutos >= 12) return "color-rojo-alerta"; // Alerta crítica de abandono en salón
        return "color-verde-activo"; // Consumo fluyendo normalmente
    }

    // ============================================================================
    // 3.2. REGLA DE LOS 3 TOQUES - MICRO-SELECTOR ELÁSTICO (TOQUE 1)
    // ============================================================================
    /**
     * TOQUE 1: Despliega un menú contextual circular para definir el segmento contable
     * sin que el mesero pierda tiempo en subcarpetas lentas de Soft Restaurant.
     */
    private detonarSelectorSegmento(mesa: MesaEstadoUI): void {
        const modalExistente = document.getElementById("micro-selector-segmento");
        if (modalExistente) modalExistente.remove();

        const microModal = document.createElement("div");
        microModal.id = "micro-selector-segmento";
        microModal.className = "micro-modal-circular";
        
        microModal.innerHTML = `
            <div class="modal-titulo">Segmentar Cuenta Mesa ${mesa.id_mesa}</div>
            <div class="opciones-grid">
                <button class="btn-seg" data-type="PUBLICO">🛒 Público General</button>
                <button class="btn-seg" data-type="SOCIO_CAVA">🍇 Socio Cava</button>
                <button class="btn-seg" data-type="INVERSIONISTA">👔 Inversionista</button>
                <button class="btn-seg" data-type="PERSONAL">👥 Menú Staff</button>
            </div>
        `;

        document.body.appendChild(microModal);

        // Captura del Toque 1 definitivo y conmutación de reglas del backend
        microModal.querySelectorAll(".btn-seg").forEach(boton => {
            boton.addEventListener("click", (e) => {
                const tipoSeleccionado = (e.target as HTMLButtonElement).getAttribute("data-type");
                console.log(`[UI TOQUE 1]: Mesa ${mesa.id_mesa} ruteada a segmento: ${tipoSeleccionado}`);
                
                // Cerrar modal y dar paso inmediato al Toque 2 (Captura de Comanda)
                microModal.remove();
                this.cargarInterfazCapturaMenu(mesa.id_mesa, tipoSeleccionado!);
            });
        });
    }

    private cargarInterfazCapturaMenu(idMesa: string, segmento: string): void {
        // Redirección interna instantánea a la cuadrícula fija 60/40 de venta asertiva
        console.log(`[UI NAVIGATE]: Desplegando cuadrícula 60/40 para Mesa ${idMesa} [Modo: ${segmento}]`);
    }
}
