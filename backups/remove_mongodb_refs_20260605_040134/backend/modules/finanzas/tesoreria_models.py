"""
Modelos para Tesorería - Cuadre de Cortes Z
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoCuadre(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    CUADRADO = "CUADRADO"
    DESCUADRE = "DESCUADRE"


class ConteoBilletes(BaseModel):
    """Conteo de billetes entregados"""
    b1000: int = Field(default=0, description="Cantidad de billetes de $1,000")
    b500: int = Field(default=0, description="Cantidad de billetes de $500")
    b200: int = Field(default=0, description="Cantidad de billetes de $200")
    b100: int = Field(default=0, description="Cantidad de billetes de $100")
    b50: int = Field(default=0, description="Cantidad de billetes de $50")
    b20: int = Field(default=0, description="Cantidad de billetes de $20")
    
    @property
    def total(self) -> float:
        return (
            self.b1000 * 1000 +
            self.b500 * 500 +
            self.b200 * 200 +
            self.b100 * 100 +
            self.b50 * 50 +
            self.b20 * 20
        )


class ConteoMonedas(BaseModel):
    """Conteo de monedas entregadas"""
    m20: int = Field(default=0, description="Cantidad de monedas de $20")
    m10: int = Field(default=0, description="Cantidad de monedas de $10")
    m5: int = Field(default=0, description="Cantidad de monedas de $5")
    m2: int = Field(default=0, description="Cantidad de monedas de $2")
    m1: int = Field(default=0, description="Cantidad de monedas de $1")
    m050: int = Field(default=0, description="Cantidad de monedas de $0.50")
    
    @property
    def total(self) -> float:
        return (
            self.m20 * 20 +
            self.m10 * 10 +
            self.m5 * 5 +
            self.m2 * 2 +
            self.m1 * 1 +
            self.m050 * 0.50
        )


class ConteoEfectivo(BaseModel):
    """Conteo completo de efectivo"""
    billetes: ConteoBilletes = Field(default_factory=ConteoBilletes)
    monedas: ConteoMonedas = Field(default_factory=ConteoMonedas)
    
    @property
    def total(self) -> float:
        return self.billetes.total + self.monedas.total


class FichaDeposito(BaseModel):
    """Datos de la ficha de depósito bancario"""
    fecha_deposito: Optional[str] = None
    banco: Optional[str] = None
    referencia: Optional[str] = None
    cuenta: Optional[str] = None
    sucursal_banco: Optional[str] = None
    importe: float = 0.0
    archivo_url: Optional[str] = None
    ocr_validado: bool = False
    ocr_data: Optional[dict] = None


class CorteZData(BaseModel):
    """Datos del Corte Z extraídos del sistema origen"""
    folio_corte: str
    fecha_corte: str
    sucursal_id: str
    sucursal_nombre: str
    fuente: str  # SOFTRESTAURANT o MPRO
    efectivo_inicial: float = 0.0
    efectivo_ventas: float = 0.0
    tarjeta: float = 0.0
    vales: float = 0.0
    otros: float = 0.0
    depositos_ef: float = 0.0
    retiros_ef: float = 0.0
    propinas_pagadas: float = 0.0
    saldo_final: float = 0.0
    efectivo_final: float = 0.0
    total_ventas: float = 0.0
    
    @property
    def monto_a_depositar(self) -> float:
        """Efectivo - Propinas Pagadas = Monto a depositar"""
        return self.efectivo_ventas - self.propinas_pagadas


class CuadreCorteZCreate(BaseModel):
    """Modelo para crear un nuevo cuadre"""
    corte_z: CorteZData
    conteo_efectivo: Optional[ConteoEfectivo] = None
    ficha_deposito: Optional[FichaDeposito] = None
    observaciones: Optional[str] = None


class CuadreCorteZUpdate(BaseModel):
    """Modelo para actualizar un cuadre"""
    conteo_efectivo: Optional[ConteoEfectivo] = None
    ficha_deposito: Optional[FichaDeposito] = None
    estado: Optional[EstadoCuadre] = None
    observaciones: Optional[str] = None
    diferencia: Optional[float] = None


class CuadreCorteZResponse(BaseModel):
    """Respuesta completa de un cuadre"""
    id: str
    corte_z: CorteZData
    conteo_efectivo: Optional[ConteoEfectivo] = None
    ficha_deposito: Optional[FichaDeposito] = None
    estado: EstadoCuadre
    monto_esperado: float
    monto_contado: float
    monto_depositado: float
    diferencia: float
    fecha_cuadre_esperada: str  # Día hábil siguiente
    validacion_fecha: bool
    observaciones: Optional[str] = None
    created_at: str
    updated_at: str
    created_by: Optional[str] = None
