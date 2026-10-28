"""Motor determinista de aforo volumetrico para botellas abiertas (Inventarios BOS).

Este modulo vive en el bounded context de Inventarios (`backend/modules/inventarios`).
Es 100% puro y determinista:
- Sin conexiones ni consultas SQL.
- Sin llamadas a servicios externos, Object Storage ni proveedores de IA.
- Sin efectos secundarios ni mutacion de estado global.

IMPORTANTE SOBRE PRECISION FISICA:
La consistencia matematica de la interpolacion (monotonia PCHIP, reproduccion exacta
de nodos y ausencia de sobrepasos numericos) NO equivale por si sola a precision fisica
en mililitros reales. La precision fisica real depende de que la curva del envase haya
sido calibrada y verificada mediante ensayos con volumenes conocidos (`verify_empirical_trials`).
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


class VolumetricEngineError(ValueError):
    """Error base determinista del motor de aforo volumetrico."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class CalibrationCurveValidationError(VolumetricEngineError):
    """La curva de calibracion viola invariantes fisicas o matematicas."""


class PhysicalBoundsError(VolumetricEngineError):
    """La lectura de entrada o el volumen resultante excede limites fisicos."""


class GravimetricParametersUnavailableError(VolumetricEngineError):
    """No existen tara o densidad fiables para ejecutar calculo gravimetrico."""


class OpaqueBottleVisualMethodError(VolumetricEngineError):
    """Una botella totalmente opaca no puede medirse por nivel visual."""


class UnvalidatedMeasurementError(VolumetricEngineError):
    """Intento de consolidar en inventario una medicion sin validacion humana."""


class CrossSectionType(str, Enum):
    CIRCULAR = "CIRCULAR"
    CUADRADA = "CUADRADA"
    RECTANGULAR = "RECTANGULAR"
    OVALADA = "OVALADA"
    FACETADA = "FACETADA"
    IRREGULAR = "IRREGULAR"


class BottleOpacity(str, Enum):
    TRANSPARENTE = "TRANSPARENTE"
    TRANSLUCIDO_OSCURO = "TRANSLUCIDO_OSCURO"
    OPACO_TOTAL = "OPACO_TOTAL"


class MeasurementMethod(str, Enum):
    VISION_ASISTIDA = "VISION_ASISTIDA"
    NIVEL_MANUAL_FOTO = "NIVEL_MANUAL_FOTO"
    GRAVIMETRICO_BASCULA = "GRAVIMETRICO_BASCULA"
    VARILLA_GRADUADA_AFORO = "VARILLA_GRADUADA_AFORO"


CANONICAL_FLUID_OUNCE_ML: float = 29.5735295625
MIN_LIQUID_DENSITY_G_PER_ML: float = 0.75
MAX_LIQUID_DENSITY_G_PER_ML: float = 1.45
MAX_CAMERA_TILT_DEG: float = 5.0
MIN_BOUNDING_SPAN_NORM: float = 0.25


def _require_finite(value: object, field_name: str, code: str = "NON_FINITE_NUMBER") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VolumetricEngineError(code, f"{field_name} debe ser numerico finito")
    as_float = float(value)
    if not math.isfinite(as_float):
        raise VolumetricEngineError(code, f"{field_name} no puede ser NaN ni infinito")
    return as_float


def _require_non_empty_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VolumetricEngineError("INVALID_IDENTIFIER", f"{field_name} es obligatorio")
    return value.strip()


@dataclass(frozen=True)
class BottleEnvelopeProfile:
    """Ficha geometrica y gravimetrica versionada de un modelo de envase."""

    producto_id: int
    envelope_model_code: str
    envelope_version: int
    nominal_capacity_ml: float
    total_exterior_height_mm: float
    nominal_fill_height_mm: float
    solid_base_height_mm: float = 0.0
    max_allowed_capacity_ml: Optional[float] = None
    presentacion_producto_id: Optional[int] = None
    cross_section_type: CrossSectionType = CrossSectionType.CIRCULAR
    opacity: BottleOpacity = BottleOpacity.TRANSPARENTE
    has_concave_punt: bool = False
    empty_tare_weight_g: Optional[float] = None
    cap_weight_g: float = 0.0
    liquid_density_g_per_ml: Optional[float] = None
    tare_uncertainty_g: float = 8.0
    inventory_unit: str = "ML"
    ml_to_inventory_unit_factor: Optional[float] = None
    calibration_verified_with_known_volumes: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.producto_id, bool) or not isinstance(self.producto_id, int) or self.producto_id <= 0:
            raise CalibrationCurveValidationError("INVALID_PRODUCTO_ID", "producto_id debe ser entero positivo")
        _require_non_empty_str(self.envelope_model_code, "envelope_model_code")
        if isinstance(self.envelope_version, bool) or not isinstance(self.envelope_version, int) or self.envelope_version < 1:
            raise CalibrationCurveValidationError("INVALID_ENVELOPE_VERSION", "envelope_version debe ser >= 1")

        nom_ml = _require_finite(self.nominal_capacity_ml, "nominal_capacity_ml")
        if nom_ml <= 0.0 or nom_ml > 20000.0:
            raise CalibrationCurveValidationError(
                "INVALID_NOMINAL_CAPACITY",
                "nominal_capacity_ml debe estar en (0, 20000]",
            )

        max_ml = (
            _require_finite(self.max_allowed_capacity_ml, "max_allowed_capacity_ml")
            if self.max_allowed_capacity_ml is not None
            else round(nom_ml * 1.02, 4)
        )
        if max_ml < nom_ml or max_ml > nom_ml * 1.05 + 1e-6:
            raise CalibrationCurveValidationError(
                "INVALID_MAX_CAPACITY",
                "max_allowed_capacity_ml debe estar entre nominal_capacity_ml y 105% de nominal_capacity_ml",
            )
        object.__setattr__(self, "max_allowed_capacity_ml", max_ml)

        h_total = _require_finite(self.total_exterior_height_mm, "total_exterior_height_mm")
        h_base = _require_finite(self.solid_base_height_mm, "solid_base_height_mm")
        h_fill = _require_finite(self.nominal_fill_height_mm, "nominal_fill_height_mm")
        if h_total < 40.0 or h_total > 800.0:
            raise CalibrationCurveValidationError(
                "INVALID_TOTAL_HEIGHT",
                "total_exterior_height_mm debe estar en [40, 800]",
            )
        if h_base < 0.0 or h_base >= h_fill:
            raise CalibrationCurveValidationError(
                "INVALID_BASE_HEIGHT",
                "solid_base_height_mm debe ser >= 0 y menor que nominal_fill_height_mm",
            )
        if h_fill <= h_base or h_fill > h_total:
            raise CalibrationCurveValidationError(
                "INVALID_FILL_HEIGHT",
                "nominal_fill_height_mm debe ser mayor a solid_base_height_mm y <= total_exterior_height_mm",
            )

        if self.empty_tare_weight_g is not None:
            tara = _require_finite(self.empty_tare_weight_g, "empty_tare_weight_g")
            if tara <= 0.0 or tara > 15000.0:
                raise CalibrationCurveValidationError(
                    "INVALID_TARE_WEIGHT",
                    "empty_tare_weight_g debe estar en (0, 15000]",
                )

        cap_w = _require_finite(self.cap_weight_g, "cap_weight_g")
        if cap_w < 0.0 or cap_w > 1000.0:
            raise CalibrationCurveValidationError("INVALID_CAP_WEIGHT", "cap_weight_g debe estar en [0, 1000]")

        if self.liquid_density_g_per_ml is not None:
            rho = _require_finite(self.liquid_density_g_per_ml, "liquid_density_g_per_ml")
            if not (MIN_LIQUID_DENSITY_G_PER_ML <= rho <= MAX_LIQUID_DENSITY_G_PER_ML):
                raise CalibrationCurveValidationError(
                    "INVALID_LIQUID_DENSITY",
                    f"liquid_density_g_per_ml debe estar en [{MIN_LIQUID_DENSITY_G_PER_ML}, {MAX_LIQUID_DENSITY_G_PER_ML}]",
                )

        tare_unc = _require_finite(self.tare_uncertainty_g, "tare_uncertainty_g")
        if tare_unc < 0.0 or tare_unc > 250.0:
            raise CalibrationCurveValidationError("INVALID_TARE_UNCERTAINTY", "tare_uncertainty_g fuera de rango")

        _require_non_empty_str(self.inventory_unit, "inventory_unit")
        if self.ml_to_inventory_unit_factor is not None:
            factor = _require_finite(self.ml_to_inventory_unit_factor, "ml_to_inventory_unit_factor")
            if factor <= 0.0:
                raise CalibrationCurveValidationError(
                    "INVALID_UNIT_CONVERSION_FACTOR",
                    "ml_to_inventory_unit_factor debe ser > 0",
                )


@dataclass(frozen=True)
class CalibrationNode:
    """Nodo empirico o CAD (h_norm, volumen_ml) de una curva de aforo."""

    relative_height_norm: float
    volume_ml: float
    node_uncertainty_ml: float = 2.0
    height_mm: Optional[float] = None

    def __post_init__(self) -> None:
        h = _require_finite(self.relative_height_norm, "relative_height_norm")
        v = _require_finite(self.volume_ml, "volume_ml")
        u = _require_finite(self.node_uncertainty_ml, "node_uncertainty_ml")
        if h < 0.0 or h > 1.0:
            raise CalibrationCurveValidationError(
                "NODE_HEIGHT_OUT_OF_RANGE",
                "relative_height_norm debe estar en [0.0, 1.0]",
            )
        if v < 0.0:
            raise CalibrationCurveValidationError(
                "NODE_NEGATIVE_VOLUME",
                "volume_ml no puede ser negativo",
            )
        if u < 0.1 or u > 500.0:
            raise CalibrationCurveValidationError(
                "NODE_INVALID_UNCERTAINTY",
                "node_uncertainty_ml debe estar en [0.1, 500.0]",
            )
        if self.height_mm is not None:
            hmm = _require_finite(self.height_mm, "height_mm")
            if hmm < 0.0:
                raise CalibrationCurveValidationError("NODE_NEGATIVE_HEIGHT_MM", "height_mm no puede ser negativo")


@dataclass(frozen=True)
class CalibrationCurve:
    """Curva de calibracion altura-volumen validada con derivadas PCHIP precalculadas."""

    profile: BottleEnvelopeProfile
    nodes: tuple[CalibrationNode, ...]
    slopes_pchip: tuple[float, ...] = ()

    def __init__(self, profile: BottleEnvelopeProfile, nodes: Sequence[CalibrationNode]) -> None:
        if not isinstance(profile, BottleEnvelopeProfile):
            raise CalibrationCurveValidationError("INVALID_PROFILE", "profile debe ser BottleEnvelopeProfile")
        if not isinstance(nodes, Sequence) or len(nodes) < 3:
            raise CalibrationCurveValidationError(
                "INSUFFICIENT_CALIBRATION_NODES",
                "La curva de calibracion requiere al menos 3 nodos",
            )
        node_tuple = tuple(nodes)
        for idx, node in enumerate(node_tuple):
            if not isinstance(node, CalibrationNode):
                raise CalibrationCurveValidationError("INVALID_NODE_TYPE", f"Nodo {idx} invalido")

        if abs(node_tuple[0].relative_height_norm - 0.0) > 1e-9 or abs(node_tuple[0].volume_ml - 0.0) > 1e-9:
            raise CalibrationCurveValidationError(
                "INVALID_LOWER_ANCHOR",
                "El nodo inicial debe anclarse exactamente en (h=0.0, V=0.0 ml)",
            )
        if abs(node_tuple[-1].relative_height_norm - 1.0) > 1e-9:
            raise CalibrationCurveValidationError(
                "INVALID_UPPER_HEIGHT_ANCHOR",
                "El nodo final debe anclarse exactamente en h=1.0",
            )
        if abs(node_tuple[-1].volume_ml - profile.nominal_capacity_ml) > 1e-4:
            raise CalibrationCurveValidationError(
                "UPPER_VOLUME_MISMATCH_NOMINAL",
                "El volumen del nodo h=1.0 debe coincidir con nominal_capacity_ml",
            )

        for i in range(len(node_tuple) - 1):
            curr_n = node_tuple[i]
            next_n = node_tuple[i + 1]
            dh = next_n.relative_height_norm - curr_n.relative_height_norm
            dv = next_n.volume_ml - curr_n.volume_ml
            if dh <= 1e-7:
                raise CalibrationCurveValidationError(
                    "NON_MONOTONIC_HEIGHT",
                    f"Las alturas relativas deben ser estrictamente crecientes (nodos {i} y {i + 1})",
                )
            if dv <= 1e-7:
                raise CalibrationCurveValidationError(
                    "NON_MONOTONIC_VOLUME",
                    f"Los volumenes deben ser estrictamente crecientes (nodos {i} y {i + 1})",
                )
            secant = dv / dh
            if secant > 15.0 * profile.nominal_capacity_ml:
                raise CalibrationCurveValidationError(
                    "UNPHYSICAL_SECANT_SLOPE",
                    f"Pendiente local excesiva entre nodos {i} y {i + 1}",
                )

        slopes = _compute_fritsch_carlson_pchip_slopes(node_tuple)
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "nodes", node_tuple)
        object.__setattr__(self, "slopes_pchip", slopes)


def _compute_fritsch_carlson_pchip_slopes(nodes: tuple[CalibrationNode, ...]) -> tuple[float, ...]:
    """Calcula las derivadas nodales d_i mediante el metodo monotono de Fritsch-Carlson (PCHIP)."""
    n = len(nodes)
    h = [nd.relative_height_norm for nd in nodes]
    v = [nd.volume_ml for nd in nodes]
    dh = [h[i + 1] - h[i] for i in range(n - 1)]
    delta = [(v[i + 1] - v[i]) / dh[i] for i in range(n - 1)]

    d = [0.0] * n
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] > 0.0:
            w1 = 2.0 * dh[i] + dh[i - 1]
            w2 = dh[i] + 2.0 * dh[i - 1]
            d[i] = (w1 + w2) / ((w1 / delta[i - 1]) + (w2 / delta[i]))
        else:
            d[i] = 0.0

    d0 = ((2.0 * dh[0] + dh[1]) * delta[0] - dh[0] * delta[1]) / (dh[0] + dh[1])
    if d0 * delta[0] <= 0.0:
        d0 = 0.0
    elif abs(d0) > 3.0 * abs(delta[0]):
        d0 = 3.0 * delta[0]
    d[0] = d0

    dn = ((2.0 * dh[-1] + dh[-2]) * delta[-1] - dh[-1] * delta[-2]) / (dh[-1] + dh[-2])
    if dn * delta[-1] <= 0.0:
        dn = 0.0
    elif abs(dn) > 3.0 * abs(delta[-1]):
        dn = 3.0 * delta[-1]
    d[-1] = dn

    return tuple(d)


@dataclass(frozen=True)
class VolumetricEstimationResult:
    """Resultado determinista de una estimacion de volumen para una botella abierta."""

    producto_id: int
    envelope_model_code: str
    envelope_version: int
    method: MeasurementMethod
    normalized_liquid_height: Optional[float]
    volume_ml: float
    remaining_pct: float
    uncertainty_ml: float
    local_sensitivity_ml_per_norm: float
    inventory_unit: str
    quantity_in_inventory_unit: float
    mathematical_interpolation_valid: bool
    empirical_accuracy_verified: bool
    human_validation_required: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnownVolumeTrial:
    """Ensayo de laboratorio con volumen real conocido (ml) y altura relativa observada."""

    observed_relative_height_norm: float
    known_true_volume_ml: float

    def __post_init__(self) -> None:
        h = _require_finite(self.observed_relative_height_norm, "observed_relative_height_norm")
        v = _require_finite(self.known_true_volume_ml, "known_true_volume_ml")
        if h < 0.0 or h > 1.0:
            raise PhysicalBoundsError("TRIAL_HEIGHT_OUT_OF_RANGE", "Altura de ensayo fuera de [0, 1]")
        if v < 0.0:
            raise PhysicalBoundsError("TRIAL_NEGATIVE_VOLUME", "Volumen conocido no puede ser negativo")


@dataclass(frozen=True)
class EmpiricalAccuracyEvaluation:
    """Resultado de contrastar la curva interpolada contra ensayos de volumen conocido."""

    trials_count: int
    max_abs_error_ml: float
    mean_abs_error_ml: float
    rmse_ml: float
    tolerance_abs_ml: float
    passed: bool


@dataclass(frozen=True)
class ValidatedOpenBottleMeasurement:
    """Lectura de botella abierta confirmada o corregida por un humano."""

    medicion_id: str
    volume_ml: float
    uncertainty_ml: float
    human_validated: bool
    validated_by_user_id: Optional[int] = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.medicion_id, "medicion_id")
        v = _require_finite(self.volume_ml, "volume_ml")
        u = _require_finite(self.uncertainty_ml, "uncertainty_ml")
        if v < 0.0:
            raise PhysicalBoundsError("NEGATIVE_VALIDATED_VOLUME", "volume_ml no puede ser negativo")
        if u < 0.0:
            raise PhysicalBoundsError("NEGATIVE_VALIDATED_UNCERTAINTY", "uncertainty_ml no puede ser negativo")


@dataclass(frozen=True)
class ConsolidatedBottleInventory:
    """Consolidacion determinista de botellas cerradas + botellas abiertas validadas."""

    producto_id: int
    envelope_model_code: str
    envelope_version: int
    closed_bottles_count: int
    open_bottles_count: int
    closed_volume_ml: float
    open_volume_ml: float
    total_volume_ml: float
    combined_uncertainty_ml: float
    inventory_unit: str
    total_quantity_in_inventory_unit: float


def normalize_liquid_height_from_frame(
    *,
    y_top_norm: float,
    y_base_norm: float,
    y_meniscus_norm: float,
    profile: BottleEnvelopeProfile,
    camera_tilt_deg: float = 0.0,
) -> float:
    """Convierte coordenadas verticales de imagen (0 arriba, 1 abajo) en altura liquida util [0, 1].

    Descuenta el espesor de la base maciza (`solid_base_height_mm`) y escala respecto
    a la columna liquida nominal (`nominal_fill_height_mm - solid_base_height_mm`).
    """
    if not isinstance(profile, BottleEnvelopeProfile):
        raise CalibrationCurveValidationError("INVALID_PROFILE", "profile debe ser BottleEnvelopeProfile")
    if profile.opacity == BottleOpacity.OPACO_TOTAL:
        raise OpaqueBottleVisualMethodError(
            "OPAQUE_BOTTLE_REQUIRES_NON_VISUAL_METHOD",
            "Las botellas totalmente opacas no admiten medicion visual del menisco",
        )

    y_top = _require_finite(y_top_norm, "y_top_norm")
    y_base = _require_finite(y_base_norm, "y_base_norm")
    y_men = _require_finite(y_meniscus_norm, "y_meniscus_norm")
    tilt = _require_finite(camera_tilt_deg, "camera_tilt_deg")

    if abs(tilt) > MAX_CAMERA_TILT_DEG:
        raise PhysicalBoundsError(
            "EXCESSIVE_CAMERA_TILT",
            f"La inclinacion de camara ({tilt:.2f} deg) supera el maximo permitido ({MAX_CAMERA_TILT_DEG:.2f} deg)",
        )
    if not (0.0 <= y_top < y_base <= 1.0):
        raise PhysicalBoundsError(
            "INVALID_FRAME_COORDINATES",
            "Se requiere 0.0 <= y_top_norm < y_base_norm <= 1.0",
        )
    span = y_base - y_top
    if span < MIN_BOUNDING_SPAN_NORM:
        raise PhysicalBoundsError(
            "INVALID_BOTTLE_BOUNDING_SPAN",
            f"La altura aparente de la botella ({span:.3f}) es menor al minimo requerido ({MIN_BOUNDING_SPAN_NORM})",
        )
    if y_men < y_top - 0.005 or y_men > y_base + 0.005:
        raise PhysicalBoundsError(
            "MENISCUS_OUTSIDE_BOTTLE_BOUNDS",
            "La coordenada del menisco se encuentra fuera de los limites verticales de la botella",
        )

    exterior_rel = max(0.0, min(1.0, (y_base - y_men) / span))
    exterior_height_mm = exterior_rel * profile.total_exterior_height_mm
    if exterior_height_mm <= profile.solid_base_height_mm:
        return 0.0

    useful_column_mm = profile.nominal_fill_height_mm - profile.solid_base_height_mm
    normalized = (exterior_height_mm - profile.solid_base_height_mm) / useful_column_mm
    if normalized > 1.05:
        raise PhysicalBoundsError(
            "MENISCUS_ABOVE_MAX_HEADSPACE",
            "El nivel detectado supera el limite fisico de llenado",
        )
    return round(min(1.0, max(0.0, normalized)), 6)


def _evaluate_pchip_with_derivative(
    curve: CalibrationCurve,
    h_norm: float,
) -> tuple[float, float, float]:
    """Evalua V(h), dV/dh(h) e incertidumbre base de calibracion sigma_cal(h) en [0, 1]."""
    nodes = curve.nodes
    slopes = curve.slopes_pchip
    h_list = [nd.relative_height_norm for nd in nodes]

    if h_norm <= 0.0:
        return 0.0, slopes[0], nodes[0].node_uncertainty_ml
    if h_norm >= 1.0:
        return curve.profile.nominal_capacity_ml, slopes[-1], nodes[-1].node_uncertainty_ml

    idx = bisect.bisect_right(h_list, h_norm) - 1
    idx = max(0, min(len(nodes) - 2, idx))

    n0 = nodes[idx]
    n1 = nodes[idx + 1]
    if abs(h_norm - n0.relative_height_norm) <= 1e-12:
        return n0.volume_ml, slopes[idx], n0.node_uncertainty_ml
    if abs(h_norm - n1.relative_height_norm) <= 1e-12:
        return n1.volume_ml, slopes[idx + 1], n1.node_uncertainty_ml

    dh = n1.relative_height_norm - n0.relative_height_norm
    t = (h_norm - n0.relative_height_norm) / dh
    t2 = t * t
    t3 = t2 * t

    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h01 = -2.0 * t3 + 3.0 * t2
    h10 = t3 - 2.0 * t2 + t
    h11 = t3 - t2

    d0 = slopes[idx]
    d1 = slopes[idx + 1]

    vol = n0.volume_ml * h00 + n1.volume_ml * h01 + dh * (d0 * h10 + d1 * h11)
    # Garantizar acotamiento monotono frente a redondeo IEEE-754 de ~1e-14
    vol = max(n0.volume_ml, min(n1.volume_ml, vol))

    dh00_dt = 6.0 * t2 - 6.0 * t
    dh01_dt = -6.0 * t2 + 6.0 * t
    dh10_dt = 3.0 * t2 - 4.0 * t + 1.0
    dh11_dt = 3.0 * t2 - 2.0 * t
    dv_dh = (n0.volume_ml * dh00_dt + n1.volume_ml * dh01_dt) / dh + d0 * dh10_dt + d1 * dh11_dt
    dv_dh = max(0.0, dv_dh)

    sigma_cal = (1.0 - t) * n0.node_uncertainty_ml + t * n1.node_uncertainty_ml
    return vol, dv_dh, sigma_cal


def convert_ml_to_canonical_unit(
    volume_ml: float,
    unit_code: str,
    *,
    nominal_capacity_ml: Optional[float] = None,
    custom_factor: Optional[float] = None,
) -> float:
    """Convierte mililitros a la unidad canonica de inventario configurada."""
    vol = _require_finite(volume_ml, "volume_ml")
    if vol < 0.0:
        raise PhysicalBoundsError("NEGATIVE_VOLUME_CONVERSION", "volume_ml no puede ser negativo")
    unit = _require_non_empty_str(unit_code, "unit_code").upper()

    if custom_factor is not None:
        factor = _require_finite(custom_factor, "custom_factor")
        if factor <= 0.0:
            raise CalibrationCurveValidationError("INVALID_CUSTOM_FACTOR", "custom_factor debe ser > 0")
        return round(vol * factor, 6)

    if unit == "ML":
        return round(vol, 6)
    if unit in ("LT", "L", "LITRO", "LITROS"):
        return round(vol / 1000.0, 6)
    if unit == "CL":
        return round(vol / 10.0, 6)
    if unit in ("ONZ", "OZ", "FL_OZ", "ONZA", "ONZAS"):
        return round(vol / CANONICAL_FLUID_OUNCE_ML, 6)
    if unit in ("PZ", "PZA", "BOT", "BOTELLA", "UNIDAD"):
        if nominal_capacity_ml is None:
            raise CalibrationCurveValidationError(
                "NOMINAL_CAPACITY_REQUIRED_FOR_PIECE_UNIT",
                f"Se requiere nominal_capacity_ml para convertir ml a {unit}",
            )
        nom = _require_finite(nominal_capacity_ml, "nominal_capacity_ml")
        if nom <= 0.0:
            raise CalibrationCurveValidationError("INVALID_NOMINAL_CAPACITY", "nominal_capacity_ml debe ser > 0")
        return round(vol / nom, 6)

    raise CalibrationCurveValidationError("UNSUPPORTED_INVENTORY_UNIT", f"Unidad no soportada: {unit}")


def estimate_volume_from_normalized_height(
    curve: CalibrationCurve,
    normalized_liquid_height: float,
    *,
    method: MeasurementMethod = MeasurementMethod.VISION_ASISTIDA,
    level_detection_confidence: Optional[float] = None,
    camera_tilt_deg: float = 0.0,
) -> VolumetricEstimationResult:
    """Calcula el volumen en ml e incertidumbre a partir de una altura normalizada [0, 1]."""
    if not isinstance(curve, CalibrationCurve):
        raise CalibrationCurveValidationError("INVALID_CURVE", "curve debe ser CalibrationCurve")
    profile = curve.profile

    if method in (MeasurementMethod.VISION_ASISTIDA, MeasurementMethod.NIVEL_MANUAL_FOTO):
        if profile.opacity == BottleOpacity.OPACO_TOTAL:
            raise OpaqueBottleVisualMethodError(
                "OPAQUE_BOTTLE_REQUIRES_NON_VISUAL_METHOD",
                "Envase OPACO_TOTAL requiere GRAVIMETRICO_BASCULA o VARILLA_GRADUADA_AFORO",
            )

    h = _require_finite(normalized_liquid_height, "normalized_liquid_height")
    if h < 0.0 or h > 1.0:
        raise PhysicalBoundsError(
            "HEIGHT_OUT_OF_RANGE",
            f"normalized_liquid_height ({h}) debe estar en [0.0, 1.0]",
        )

    tilt = _require_finite(camera_tilt_deg, "camera_tilt_deg")
    if abs(tilt) > MAX_CAMERA_TILT_DEG:
        raise PhysicalBoundsError(
            "EXCESSIVE_CAMERA_TILT",
            f"camera_tilt_deg ({tilt}) excede el limite de {MAX_CAMERA_TILT_DEG} grados",
        )

    conf = 0.92
    if level_detection_confidence is not None:
        conf = _require_finite(level_detection_confidence, "level_detection_confidence")
        if not (0.0 <= conf <= 1.0):
            raise PhysicalBoundsError(
                "INVALID_CONFIDENCE_RANGE",
                "level_detection_confidence debe estar en [0.0, 1.0]",
            )

    vol_raw, dv_dh, sigma_cal = _evaluate_pchip_with_derivative(curve, h)
    max_cap = float(profile.max_allowed_capacity_ml or profile.nominal_capacity_ml)
    if vol_raw < -1e-9 or vol_raw > max_cap + 1e-6:
        raise PhysicalBoundsError(
            "INTERPOLATED_VOLUME_OUT_OF_BOUNDS",
            "El volumen interpolado excede los limites permitidos del envase",
        )
    vol_ml = round(max(0.0, min(profile.nominal_capacity_ml, vol_raw)), 2)
    pct = round(max(0.0, min(100.0, (vol_ml / profile.nominal_capacity_ml) * 100.0)), 2)

    if method == MeasurementMethod.VISION_ASISTIDA:
        sigma_h = max(0.008, 0.03 * (1.0 - conf))
    elif method == MeasurementMethod.NIVEL_MANUAL_FOTO:
        sigma_h = 0.012
    else:
        sigma_h = 0.006

    if profile.opacity == BottleOpacity.TRANSLUCIDO_OSCURO:
        sigma_h *= 1.35

    sigma_tilt = 0.004 * profile.nominal_capacity_ml * abs(tilt)
    uncertainty_ml = round(
        math.sqrt((sigma_cal ** 2) + ((dv_dh * sigma_h) ** 2) + (sigma_tilt ** 2)),
        2,
    )

    warnings: list[str] = []
    if not profile.calibration_verified_with_known_volumes:
        warnings.append("CURVA_SIN_ENSAYO_FISICO_CERTIFICADO")
    if method == MeasurementMethod.VISION_ASISTIDA and conf < 0.85:
        warnings.append("CONFIANZA_DETECCION_BAJA_REQUIERE_AJUSTE_MANUAL")
    if profile.opacity == BottleOpacity.TRANSLUCIDO_OSCURO:
        warnings.append("ENVASE_OSCURO_RECOMIENDA_CONTRALUZ_O_BASCULA")

    qty_unit = convert_ml_to_canonical_unit(
        vol_ml,
        profile.inventory_unit,
        nominal_capacity_ml=profile.nominal_capacity_ml,
        custom_factor=profile.ml_to_inventory_unit_factor,
    )

    return VolumetricEstimationResult(
        producto_id=profile.producto_id,
        envelope_model_code=profile.envelope_model_code,
        envelope_version=profile.envelope_version,
        method=method,
        normalized_liquid_height=round(h, 6),
        volume_ml=vol_ml,
        remaining_pct=pct,
        uncertainty_ml=uncertainty_ml,
        local_sensitivity_ml_per_norm=round(dv_dh, 2),
        inventory_unit=profile.inventory_unit.upper(),
        quantity_in_inventory_unit=qty_unit,
        mathematical_interpolation_valid=True,
        empirical_accuracy_verified=profile.calibration_verified_with_known_volumes,
        human_validation_required=True,
        warnings=tuple(warnings),
    )


def estimate_volume_gravimetric(
    profile: BottleEnvelopeProfile,
    gross_weight_g: float,
    *,
    include_cap: bool = False,
    scale_uncertainty_g: float = 1.0,
) -> VolumetricEstimationResult:
    """Calcula el volumen en ml mediante pesaje en bascula cuando existen tara y densidad fiables."""
    if not isinstance(profile, BottleEnvelopeProfile):
        raise CalibrationCurveValidationError("INVALID_PROFILE", "profile debe ser BottleEnvelopeProfile")
    if profile.empty_tare_weight_g is None or profile.liquid_density_g_per_ml is None:
        raise GravimetricParametersUnavailableError(
            "MISSING_TARE_OR_DENSITY",
            "El envase no cuenta con empty_tare_weight_g y liquid_density_g_per_ml configurados",
        )

    gross_g = _require_finite(gross_weight_g, "gross_weight_g")
    scale_unc_g = _require_finite(scale_uncertainty_g, "scale_uncertainty_g")
    if gross_g <= 0.0:
        raise PhysicalBoundsError("INVALID_GROSS_WEIGHT", "gross_weight_g debe ser > 0")
    if scale_unc_g < 0.1 or scale_unc_g > 100.0:
        raise PhysicalBoundsError("INVALID_SCALE_UNCERTAINTY", "scale_uncertainty_g debe estar en [0.1, 100.0]")

    tare_total_g = profile.empty_tare_weight_g + (profile.cap_weight_g if include_cap else 0.0)
    net_liquid_g = gross_g - tare_total_g

    if net_liquid_g < -5.0:
        raise PhysicalBoundsError(
            "GROSS_WEIGHT_BELOW_TARE",
            f"El peso bruto ({gross_g:.2f} g) es inferior a la tara ({tare_total_g:.2f} g)",
        )
    if net_liquid_g <= 0.0:
        vol_ml = 0.0
    else:
        vol_raw = net_liquid_g / profile.liquid_density_g_per_ml
        max_cap = float(profile.max_allowed_capacity_ml or profile.nominal_capacity_ml)
        if vol_raw > max_cap:
            raise PhysicalBoundsError(
                "CALCULATED_VOLUME_EXCEEDS_MAX_CAPACITY",
                f"El volumen gravimetrico ({vol_raw:.2f} ml) supera el maximo permitido ({max_cap:.2f} ml)",
            )
        vol_ml = round(min(profile.nominal_capacity_ml, vol_raw), 2)

    pct = round(max(0.0, min(100.0, (vol_ml / profile.nominal_capacity_ml) * 100.0)), 2)
    uncertainty_ml = round(
        math.sqrt((profile.tare_uncertainty_g ** 2) + (scale_unc_g ** 2)) / profile.liquid_density_g_per_ml,
        2,
    )
    qty_unit = convert_ml_to_canonical_unit(
        vol_ml,
        profile.inventory_unit,
        nominal_capacity_ml=profile.nominal_capacity_ml,
        custom_factor=profile.ml_to_inventory_unit_factor,
    )

    warnings: list[str] = []
    if not profile.calibration_verified_with_known_volumes:
        warnings.append("CURVA_SIN_ENSAYO_FISICO_CERTIFICADO")

    return VolumetricEstimationResult(
        producto_id=profile.producto_id,
        envelope_model_code=profile.envelope_model_code,
        envelope_version=profile.envelope_version,
        method=MeasurementMethod.GRAVIMETRICO_BASCULA,
        normalized_liquid_height=None,
        volume_ml=vol_ml,
        remaining_pct=pct,
        uncertainty_ml=uncertainty_ml,
        local_sensitivity_ml_per_norm=round(1.0 / profile.liquid_density_g_per_ml, 4),
        inventory_unit=profile.inventory_unit.upper(),
        quantity_in_inventory_unit=qty_unit,
        mathematical_interpolation_valid=True,
        empirical_accuracy_verified=profile.calibration_verified_with_known_volumes,
        human_validation_required=True,
        warnings=tuple(warnings),
    )


def verify_empirical_trials(
    curve: CalibrationCurve,
    trials: Sequence[KnownVolumeTrial],
    *,
    tolerance_abs_ml: float = 10.0,
) -> EmpiricalAccuracyEvaluation:
    """Evalua la precision fisica real de una curva frente a ensayos independientes con volumenes conocidos."""
    if not isinstance(curve, CalibrationCurve):
        raise CalibrationCurveValidationError("INVALID_CURVE", "curve debe ser CalibrationCurve")
    if not isinstance(trials, Sequence) or len(trials) == 0:
        raise CalibrationCurveValidationError("EMPTY_TRIALS", "Se requiere al menos un ensayo con volumen conocido")
    tol = _require_finite(tolerance_abs_ml, "tolerance_abs_ml")
    if tol <= 0.0:
        raise CalibrationCurveValidationError("INVALID_TOLERANCE", "tolerance_abs_ml debe ser > 0")

    abs_errors: list[float] = []
    for trial in trials:
        if not isinstance(trial, KnownVolumeTrial):
            raise CalibrationCurveValidationError("INVALID_TRIAL_ITEM", "Cada elemento debe ser KnownVolumeTrial")
        est = estimate_volume_from_normalized_height(
            curve,
            trial.observed_relative_height_norm,
            method=MeasurementMethod.VARILLA_GRADUADA_AFORO,
        )
        abs_errors.append(abs(est.volume_ml - trial.known_true_volume_ml))

    max_err = round(max(abs_errors), 4)
    mean_err = round(sum(abs_errors) / len(abs_errors), 4)
    rmse = round(math.sqrt(sum(e * e for e in abs_errors) / len(abs_errors)), 4)

    return EmpiricalAccuracyEvaluation(
        trials_count=len(abs_errors),
        max_abs_error_ml=max_err,
        mean_abs_error_ml=mean_err,
        rmse_ml=rmse,
        tolerance_abs_ml=tol,
        passed=max_err <= tol,
    )


def consolidate_bottle_inventory(
    profile: BottleEnvelopeProfile,
    *,
    closed_bottles_count: int,
    open_measurements: Sequence[ValidatedOpenBottleMeasurement],
) -> ConsolidatedBottleInventory:
    """Consolida botellas cerradas + botellas abiertas validadas por humano hacia la unidad de inventario."""
    if not isinstance(profile, BottleEnvelopeProfile):
        raise CalibrationCurveValidationError("INVALID_PROFILE", "profile debe ser BottleEnvelopeProfile")
    if isinstance(closed_bottles_count, bool) or not isinstance(closed_bottles_count, int) or closed_bottles_count < 0:
        raise PhysicalBoundsError("INVALID_CLOSED_BOTTLES_COUNT", "closed_bottles_count debe ser entero >= 0")

    seen_ids: set[str] = set()
    open_vol_ml = 0.0
    open_var_ml2 = 0.0

    for item in open_measurements:
        if not isinstance(item, ValidatedOpenBottleMeasurement):
            raise UnvalidatedMeasurementError("INVALID_MEASUREMENT_ITEM", "Elemento de medicion invalido")
        if not item.human_validated or item.validated_by_user_id is None or item.validated_by_user_id <= 0:
            raise UnvalidatedMeasurementError(
                "HUMAN_VALIDATION_REQUIRED",
                f"La medicion {item.medicion_id} no cuenta con validacion humana autorizada",
            )
        if item.medicion_id in seen_ids:
            raise PhysicalBoundsError("DUPLICATE_MEASUREMENT_ID", f"Medicion duplicada: {item.medicion_id}")
        max_cap = float(profile.max_allowed_capacity_ml or profile.nominal_capacity_ml)
        if item.volume_ml > max_cap:
            raise PhysicalBoundsError(
                "OPEN_BOTTLE_EXCEEDS_MAX_CAPACITY",
                f"La medicion {item.medicion_id} ({item.volume_ml} ml) excede la capacidad maxima ({max_cap} ml)",
            )
        seen_ids.add(item.medicion_id)
        open_vol_ml += item.volume_ml
        open_var_ml2 += item.uncertainty_ml ** 2

    closed_vol_ml = round(closed_bottles_count * profile.nominal_capacity_ml, 2)
    open_vol_ml = round(open_vol_ml, 2)
    total_vol_ml = round(closed_vol_ml + open_vol_ml, 2)
    combined_unc_ml = round(math.sqrt(open_var_ml2), 2)

    total_qty = convert_ml_to_canonical_unit(
        total_vol_ml,
        profile.inventory_unit,
        nominal_capacity_ml=profile.nominal_capacity_ml,
        custom_factor=profile.ml_to_inventory_unit_factor,
    )

    return ConsolidatedBottleInventory(
        producto_id=profile.producto_id,
        envelope_model_code=profile.envelope_model_code,
        envelope_version=profile.envelope_version,
        closed_bottles_count=closed_bottles_count,
        open_bottles_count=len(open_measurements),
        closed_volume_ml=closed_vol_ml,
        open_volume_ml=open_vol_ml,
        total_volume_ml=total_vol_ml,
        combined_uncertainty_ml=combined_unc_ml,
        inventory_unit=profile.inventory_unit.upper(),
        total_quantity_in_inventory_unit=total_qty,
    )
