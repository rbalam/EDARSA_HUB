from __future__ import annotations

from core.bos_program_status import FrontSpec, MilestoneSpec


BOS_V1_GATE_A_JOB_IDS = (
    'BOS-V1-GATE-A-FOUNDATION-CERTIFICATION',
)
BOS_V1_GATE_B_JOB_IDS = (
    'BOS-V1-GATE-B-AUTONOMOUS-OPERATIONS-CERTIFICATION',
)
BOS_V1_GATE_C_JOB_IDS = (
    'BOS-V1-GATE-C-FUNCTIONAL-COVERAGE-CERTIFICATION',
)
BOS_V1_GATE_D_JOB_IDS = (
    'BOS-V1-GATE-D-GOVERNANCE-CERTIFICATION',
)
BOS_V1_GATE_E_JOB_IDS = (
    'BOS-V1-GATE-E-EXECUTIVE-BOS-CERTIFICATION',
)
BOS_V1_GATE_F_JOB_IDS = (
    'BOS-V1-GATE-F-INTELLIGENCE-CERTIFICATION',
)
BOS_V1_GATE_G_JOB_IDS = (
    'BOS-V1-GATE-G-V1-FINAL-CERTIFICATION',
)


BOS_V1_FRONTS = (
    FrontSpec(
        front_id='foundation_architecture',
        milestones=(
            MilestoneSpec(
                milestone_id='gate_a_foundation',
                evidence_job_ids=BOS_V1_GATE_A_JOB_IDS,
            ),
        ),
    ),
    FrontSpec(
        front_id='automation_autonomous_operations',
        milestones=(
            MilestoneSpec(
                milestone_id='gate_b_autonomous_operations',
                evidence_job_ids=BOS_V1_GATE_B_JOB_IDS,
            ),
        ),
    ),
    FrontSpec(
        front_id='data_kpis_business_domains',
        milestones=(
            MilestoneSpec(
                milestone_id='gate_c_functional_coverage',
                evidence_job_ids=BOS_V1_GATE_C_JOB_IDS,
            ),
            MilestoneSpec(
                milestone_id='gate_e_executive_bos',
                evidence_job_ids=BOS_V1_GATE_E_JOB_IDS,
            ),
        ),
    ),
    FrontSpec(
        front_id='security_rbac_policy_governance',
        milestones=(
            MilestoneSpec(
                milestone_id='gate_d_governance',
                evidence_job_ids=BOS_V1_GATE_D_JOB_IDS,
            ),
        ),
    ),
    FrontSpec(
        front_id='intelligence_prediction_governed_autonomy',
        milestones=(
            MilestoneSpec(
                milestone_id='gate_f_intelligence',
                evidence_job_ids=BOS_V1_GATE_F_JOB_IDS,
            ),
            MilestoneSpec(
                milestone_id='gate_g_final_v1_certification',
                evidence_job_ids=BOS_V1_GATE_G_JOB_IDS,
            ),
        ),
    ),
)


def bos_v1_fronts() -> tuple[FrontSpec, ...]:
    return BOS_V1_FRONTS
