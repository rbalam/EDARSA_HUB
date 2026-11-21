"""Suite de pruebas unitarias deterministas para el motor volumetrico de botellas (Gate 3A).

Cubre:
- Curvas monotonas y rechazo de curvas no monotonas.
- Control de capacidad nominal y limites fisicos.
- Alturas fuera de rango e inclinacion excesiva de camara.
- Geometria con base gruesa, fondo concavo (punt) y cuello estrecho.
- Interpolacion PCHIP entre puntos conocidos y reproduccion nodal exacta.
- Ausencia total de sobrepasos numericos (overshoot) en malla fina.
- Propagacion determinista de incertidumbre.
- Rechazo de NaN, infinitos, booleanos y valores invalidos.
- Conversion a unidades canonicas (ML, LT, CL, ONZ, PZ/BOT y factor personalizado).
- Calculo gravimetrico alternativo para botellas opacas (solo con tara y densidad fiables).
- Distincion entre interpolacion matematica y precision fisica verificada por ensayos.
- Consolidacion con validacion humana obligatoria y no-regresion de inventarios existentes.
"""
from __future__ import annotations

import math
import pytest

from modules.inventarios.bottle_volumetric_engine import (
    BottleEnvelopeProfile,
    BottleOpacity,
    CalibrationCurve,
    CalibrationCurveValidationError,
    CalibrationNode,
    CrossSectionType,
    GravimetricParametersUnavailableError,
    KnownVolumeTrial,
    MeasurementMethod,
    OpaqueBottleVisualMethodError,
    PhysicalBoundsError,
    UnvalidatedMeasurementError,
    ValidatedOpenBottleMeasurement,
    VolumetricEngineError,
    consolidate_bottle_inventory,
    convert_ml_to_canonical_unit,
    estimate_volume_from_normalized_height,
    estimate_volume_gravimetric,
    normalize_liquid_height_from_frame,
    verify_empirical_trials,
)


def _sample_750ml_profile(
    *,
    opacity: BottleOpacity = BottleOpacity.TRANSPARENTE,
    inventory_unit: str = "ML",
    verified_trials: bool = False,
    tare_g: float | None = 520.0,
    density_g_ml: float | None = 0.948,
) -> BottleEnvelopeProfile:
    """Perfil de botella de 750 ml con base maciza de 25 mm, punt concavo y cuello estrecho."""
    return BottleEnvelopeProfile(
        producto_id=1042,
        presentacion_producto_id=5012,
        envelope_model_code="TEQ-REP-750ML-V1",
        envelope_version=1,
        nominal_capacity_ml=750.0,
        max_allowed_capacity_ml=765.0,
        total_exterior_height_mm=305.0,
        solid_base_height_mm=25.0,
        nominal_fill_height_mm=275.0,
        cross_section_type=CrossSectionType.CIRCULAR,
        opacity=opacity,
        has_concave_punt=True,
        empty_tare_weight_g=tare_g,
        cap_weight_g=18.5,
        liquid_density_g_per_ml=density_g_ml,
        tare_uncertainty_g=6.0,
        inventory_unit=inventory_unit,
        calibration_verified_with_known_volumes=verified_trials,
    )


def _sample_750ml_curve(
    *,
    opacity: BottleOpacity = BottleOpacity.TRANSPARENTE,
    inventory_unit: str = "ML",
    verified_trials: bool = False,
) -> CalibrationCurve:
    """Curva no lineal realista de 750 ml:
    - Tramo inferior (0.00 a 0.15): menor volumen por mm debido al punt concavo (65 ml).
    - Cuerpo principal (0.15 a 0.72): seccion ancha (~575 ml acumulados -> 640 ml).
    - Hombro y cuello estrecho (0.72 a 1.00): seccion se reduce drasticamente (de 640 a 750 ml).
    """
    profile = _sample_750ml_profile(
        opacity=opacity,
        inventory_unit=inventory_unit,
        verified_trials=verified_trials,
    )
    nodes = (
        CalibrationNode(0.00, 0.0, node_uncertainty_ml=1.5),
        CalibrationNode(0.10, 38.0, node_uncertainty_ml=2.0),
        CalibrationNode(0.20, 105.0, node_uncertainty_ml=2.5),
        CalibrationNode(0.40, 310.0, node_uncertainty_ml=3.0),
        CalibrationNode(0.60, 520.0, node_uncertainty_ml=3.0),
        CalibrationNode(0.72, 640.0, node_uncertainty_ml=2.5),
        CalibrationNode(0.85, 712.0, node_uncertainty_ml=1.8),
        CalibrationNode(0.95, 740.0, node_uncertainty_ml=1.2),
        CalibrationNode(1.00, 750.0, node_uncertainty_ml=1.0),
    )
    return CalibrationCurve(profile=profile, nodes=nodes)


def test_valid_monotonic_curve_and_exact_nodal_reproduction() -> None:
    curve = _sample_750ml_curve()
    for node in curve.nodes:
        res = estimate_volume_from_normalized_height(
            curve,
            node.relative_height_norm,
            method=MeasurementMethod.VISION_ASISTIDA,
            level_detection_confidence=0.95,
        )
        assert res.volume_ml == pytest.approx(node.volume_ml, abs=1e-2)
        assert res.mathematical_interpolation_valid is True
        assert res.human_validation_required is True
        # Al no tener verified_trials=True, no afirma precision fisica certificada
        assert res.empirical_accuracy_verified is False
        assert "CURVA_SIN_ENSAYO_FISICO_CERTIFICADO" in res.warnings


def test_rejects_non_monotonic_and_invalid_anchor_curves() -> None:
    profile = _sample_750ml_profile()

    # Menos de 3 nodos
    with pytest.raises(CalibrationCurveValidationError) as exc_few:
        CalibrationCurve(
            profile,
            [CalibrationNode(0.0, 0.0), CalibrationNode(1.0, 750.0)],
        )
    assert exc_few.value.code == "INSUFFICIENT_CALIBRATION_NODES"

    # Anclaje inferior distinto de (0, 0)
    with pytest.raises(CalibrationCurveValidationError) as exc_low:
        CalibrationCurve(
            profile,
            [
                CalibrationNode(0.0, 10.0),
                CalibrationNode(0.5, 375.0),
                CalibrationNode(1.0, 750.0),
            ],
        )
    assert exc_low.value.code == "INVALID_LOWER_ANCHOR"

    # Anclaje superior no coincide con nominal_capacity_ml
    with pytest.raises(CalibrationCurveValidationError) as exc_high:
        CalibrationCurve(
            profile,
            [
                CalibrationNode(0.0, 0.0),
                CalibrationNode(0.5, 375.0),
                CalibrationNode(1.0, 700.0),
            ],
        )
    assert exc_high.value.code == "UPPER_VOLUME_MISMATCH_NOMINAL"

    # Alturas no monotonas (repetidas o decrecientes)
    with pytest.raises(CalibrationCurveValidationError) as exc_h:
        CalibrationCurve(
            profile,
            [
                CalibrationNode(0.0, 0.0),
                CalibrationNode(0.5, 300.0),
                CalibrationNode(0.5, 450.0),
                CalibrationNode(1.0, 750.0),
            ],
        )
    assert exc_h.value.code == "NON_MONOTONIC_HEIGHT"

    # Volumenes no monotonos (estancados o decrecientes)
    with pytest.raises(CalibrationCurveValidationError) as exc_v:
        CalibrationCurve(
            profile,
            [
                CalibrationNode(0.0, 0.0),
                CalibrationNode(0.4, 420.0),
                CalibrationNode(0.7, 390.0),
                CalibrationNode(1.0, 750.0),
            ],
        )
    assert exc_v.value.code == "NON_MONOTONIC_VOLUME"


def test_pchip_monotonicity_and_zero_overshoot_across_dense_grid() -> None:
    """Verifica ausencia total de sobrepasos (overshoot) en 1,000 puntos entre [0, 1]."""
    curve = _sample_750ml_curve()
    prev_v = -1.0
    for step in range(0, 1001):
        h = step / 1000.0
        res = estimate_volume_from_normalized_height(curve, h)
        assert 0.0 <= res.volume_ml <= 750.0
        assert res.volume_ml >= prev_v
        prev_v = res.volume_ml


def test_thick_base_and_narrow_neck_geometry_effects() -> None:
    """Verifica descuento de base maciza (25 mm) y menor sensibilidad dV/dh en cuello estrecho."""
    curve = _sample_750ml_curve()
    profile = curve.profile

    # Un nivel aparente a 20 mm de la base exterior cae dentro del vidrio macizo (25 mm) -> h_norm = 0.0 -> 0 ml
    y_top = 0.10
    y_base = 0.90
    span = y_base - y_top
    y_meniscus_in_glass_base = y_base - (20.0 / profile.total_exterior_height_mm) * span
    h_norm_base = normalize_liquid_height_from_frame(
        y_top_norm=y_top,
        y_base_norm=y_base,
        y_meniscus_norm=y_meniscus_in_glass_base,
        profile=profile,
    )
    assert h_norm_base == 0.0
    assert estimate_volume_from_normalized_height(curve, h_norm_base).volume_ml == 0.0

    # Sensibilidad local dV/dh en el cuerpo ancho (h=0.50) vs en el cuello estrecho (h=0.92)
    body_est = estimate_volume_from_normalized_height(curve, 0.50)
    neck_est = estimate_volume_from_normalized_height(curve, 0.92)
    assert body_est.local_sensitivity_ml_per_norm > 900.0
    assert neck_est.local_sensitivity_ml_per_norm < 350.0
    assert body_est.uncertainty_ml > neck_est.uncertainty_ml

    # En h=0.72 (inicio de hombro), una botella con cuello estrecho ya acumula 640 ml (85.33%),
    # demostrando que una regla lineal 2D (0.72 * 750 = 540 ml) subestimaria por 100 ml
    shoulder_est = estimate_volume_from_normalized_height(curve, 0.72)
    assert shoulder_est.volume_ml == pytest.approx(640.0, abs=0.05)
    assert shoulder_est.remaining_pct == pytest.approx(85.33, abs=0.05)


def test_out_of_range_heights_and_camera_tilt_rejected() -> None:
    curve = _sample_750ml_curve()
    with pytest.raises(PhysicalBoundsError) as exc_neg:
        estimate_volume_from_normalized_height(curve, -0.01)
    assert exc_neg.value.code == "HEIGHT_OUT_OF_RANGE"

    with pytest.raises(PhysicalBoundsError) as exc_over:
        estimate_volume_from_normalized_height(curve, 1.01)
    assert exc_over.value.code == "HEIGHT_OUT_OF_RANGE"

    with pytest.raises(PhysicalBoundsError) as exc_tilt:
        estimate_volume_from_normalized_height(curve, 0.50, camera_tilt_deg=6.2)
    assert exc_tilt.value.code == "EXCESSIVE_CAMERA_TILT"

    with pytest.raises(PhysicalBoundsError) as exc_span:
        normalize_liquid_height_from_frame(
            y_top_norm=0.40,
            y_base_norm=0.55,
            y_meniscus_norm=0.48,
            profile=curve.profile,
        )
    assert exc_span.value.code == "INVALID_BOTTLE_BOUNDING_SPAN"


def test_uncertainty_propagation_with_confidence_tilt_and_opacity() -> None:
    curve_clear = _sample_750ml_curve(opacity=BottleOpacity.TRANSPARENTE)
    curve_dark = _sample_750ml_curve(opacity=BottleOpacity.TRANSLUCIDO_OSCURO)

    high_conf = estimate_volume_from_normalized_height(
        curve_clear, 0.50, level_detection_confidence=0.98, camera_tilt_deg=0.0
    )
    low_conf = estimate_volume_from_normalized_height(
        curve_clear, 0.50, level_detection_confidence=0.70, camera_tilt_deg=0.0
    )
    tilted = estimate_volume_from_normalized_height(
        curve_clear, 0.50, level_detection_confidence=0.98, camera_tilt_deg=4.5
    )
    dark_glass = estimate_volume_from_normalized_height(
        curve_dark, 0.50, level_detection_confidence=0.98, camera_tilt_deg=0.0
    )

    assert low_conf.uncertainty_ml > high_conf.uncertainty_ml
    assert "CONFIANZA_DETECCION_BAJA_REQUIERE_AJUSTE_MANUAL" in low_conf.warnings
    assert tilted.uncertainty_ml > high_conf.uncertainty_ml
    assert dark_glass.uncertainty_ml > high_conf.uncertainty_ml
    assert "ENVASE_OSCURO_RECOMIENDA_CONTRALUZ_O_BASCULA" in dark_glass.warnings


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf, True, False, "0.5", None])
def test_rejects_nan_inf_and_invalid_types(bad_value: object) -> None:
    curve = _sample_750ml_curve()
    with pytest.raises(VolumetricEngineError):
        estimate_volume_from_normalized_height(curve, bad_value)  # type: ignore[arg-type]

    with pytest.raises(VolumetricEngineError):
        CalibrationNode(bad_value, 100.0)  # type: ignore[arg-type]


def test_opaque_bottle_blocks_visual_and_computes_gravimetric() -> None:
    opaque_curve = _sample_750ml_curve(opacity=BottleOpacity.OPACO_TOTAL)
    opaque_profile = opaque_curve.profile

    with pytest.raises(OpaqueBottleVisualMethodError) as exc_vis:
        estimate_volume_from_normalized_height(
            opaque_curve, 0.50, method=MeasurementMethod.VISION_ASISTIDA
        )
    assert exc_vis.value.code == "OPAQUE_BOTTLE_REQUIRES_NON_VISUAL_METHOD"

    with pytest.raises(OpaqueBottleVisualMethodError):
        normalize_liquid_height_from_frame(
            y_top_norm=0.1,
            y_base_norm=0.9,
            y_meniscus_norm=0.5,
            profile=opaque_profile,
        )

    # Calculo gravimetrico exacto: tara=520 g, tapon=18.5 g, densidad=0.948 g/ml
    # Para 400 ml reales -> masa liquido = 379.2 g -> peso bruto con tapon = 520 + 18.5 + 379.2 = 917.7 g
    grav_res = estimate_volume_gravimetric(
        opaque_profile,
        gross_weight_g=917.7,
        include_cap=True,
        scale_uncertainty_g=1.0,
    )
    assert grav_res.volume_ml == pytest.approx(400.0, abs=0.05)
    assert grav_res.remaining_pct == pytest.approx(53.33, abs=0.05)
    assert grav_res.method == MeasurementMethod.GRAVIMETRICO_BASCULA
    assert grav_res.uncertainty_ml > 0.0

    # Rechazo cuando el peso bruto es inferior a la tara
    with pytest.raises(PhysicalBoundsError) as exc_under:
        estimate_volume_gravimetric(opaque_profile, gross_weight_g=490.0, include_cap=False)
    assert exc_under.value.code == "GROSS_WEIGHT_BELOW_TARE"

    # Rechazo cuando faltan tara o densidad
    profile_no_tare = _sample_750ml_profile(
        opacity=BottleOpacity.OPACO_TOTAL, tare_g=None, density_g_ml=0.948
    )
    with pytest.raises(GravimetricParametersUnavailableError) as exc_missing:
        estimate_volume_gravimetric(profile_no_tare, gross_weight_g=900.0)
    assert exc_missing.value.code == "MISSING_TARE_OR_DENSITY"


def test_empirical_accuracy_verification_against_known_volumes() -> None:
    """Demuestra que la precision fisica se evalua contra ensayos reales de volumen conocido."""
    curve = _sample_750ml_curve(verified_trials=True)
    trials = [
        KnownVolumeTrial(observed_relative_height_norm=0.15, known_true_volume_ml=68.5),
        KnownVolumeTrial(observed_relative_height_norm=0.30, known_true_volume_ml=205.0),
        KnownVolumeTrial(observed_relative_height_norm=0.50, known_true_volume_ml=415.0),
        KnownVolumeTrial(observed_relative_height_norm=0.80, known_true_volume_ml=687.0),
    ]
    eval_pass = verify_empirical_trials(curve, trials, tolerance_abs_ml=5.0)
    assert eval_pass.passed is True
    assert eval_pass.trials_count == 4
    assert eval_pass.max_abs_error_ml <= 5.0

    # Si un ensayo real difiere por 45 ml (ej. botella de otro molde), falla la verificacion empirica
    bad_trials = [
        KnownVolumeTrial(observed_relative_height_norm=0.50, known_true_volume_ml=465.0),
    ]
    eval_fail = verify_empirical_trials(curve, bad_trials, tolerance_abs_ml=10.0)
    assert eval_fail.passed is False
    assert eval_fail.max_abs_error_ml > 40.0


def test_unit_conversions_and_inventory_consolidation_requires_human_validation() -> None:
    assert convert_ml_to_canonical_unit(750.0, "ML") == 750.0
    assert convert_ml_to_canonical_unit(1500.0, "LT") == 1.5
    assert convert_ml_to_canonical_unit(750.0, "CL") == 75.0
    assert convert_ml_to_canonical_unit(295.735295625, "ONZ") == pytest.approx(10.0, abs=1e-5)
    assert convert_ml_to_canonical_unit(375.0, "PZ", nominal_capacity_ml=750.0) == 0.5

    profile_lt = _sample_750ml_profile(inventory_unit="LT")
    open_ok = [
        ValidatedOpenBottleMeasurement(
            medicion_id="MED-001",
            volume_ml=412.5,
            uncertainty_ml=4.0,
            human_validated=True,
            validated_by_user_id=8,
        ),
        ValidatedOpenBottleMeasurement(
            medicion_id="MED-002",
            volume_ml=187.5,
            uncertainty_ml=3.0,
            human_validated=True,
            validated_by_user_id=8,
        ),
    ]
    consolidated = consolidate_bottle_inventory(
        profile_lt,
        closed_bottles_count=3,
        open_measurements=open_ok,
    )
    assert consolidated.closed_volume_ml == 2250.0
    assert consolidated.open_volume_ml == 600.0
    assert consolidated.total_volume_ml == 2850.0
    assert consolidated.combined_uncertainty_ml == 5.0
    assert consolidated.total_quantity_in_inventory_unit == 2.85

    # Prohibicion de consolidar mediciones sin validacion humana
    with pytest.raises(UnvalidatedMeasurementError) as exc_unval:
        consolidate_bottle_inventory(
            profile_lt,
            closed_bottles_count=1,
            open_measurements=[
                ValidatedOpenBottleMeasurement(
                    medicion_id="MED-UNVAL",
                    volume_ml=300.0,
                    uncertainty_ml=5.0,
                    human_validated=False,
                    validated_by_user_id=None,
                )
            ],
        )
    assert exc_unval.value.code == "HUMAN_VALIDATION_REQUIRED"


def test_existing_inventarios_contracts_no_regression() -> None:
    """Verifica que los contratos existentes de inventarios y auditoria ciega siguen intactos."""
    from core.inventarios.contracts import build_normalized_inventory_request
    from modules.cava_socios.blind_audit import BlindObservation, ExpectedBottle, reconcile_blind_audit

    req = build_normalized_inventory_request(
        {"folios_iniciales": ["F-001"], "folios_finales": ["F-002"]},
        server_id="SRV-130QRO",
    )
    assert req.server_id == "SRV-130QRO"
    assert req.lista_folios_ini == ["F-001"]
    assert req.lista_folios_fin == ["F-002"]

    audit = reconcile_blind_audit(
        expected=[ExpectedBottle(bottle_id="BOT-1", expected_quantity=1, expected_level_pct=50.0)],
        observations=[
            BlindObservation(
                observation_id="OBS-1",
                observed_reference="REF-1",
                observed_quantity=1,
                observed_level_pct=50.0,
                evidence_id="EV-1",
                recognition_confidence=0.95,
            )
        ],
        observation_to_bottle={"OBS-1": "BOT-1"},
    )
    assert audit.clean is True
