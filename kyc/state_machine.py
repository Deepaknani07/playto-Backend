from kyc.models import KYCState

LEGAL_TRANSITIONS = {
    KYCState.DRAFT: {KYCState.SUBMITTED},
    KYCState.SUBMITTED: {KYCState.UNDER_REVIEW},
    KYCState.UNDER_REVIEW: {KYCState.APPROVED, KYCState.REJECTED, KYCState.MORE_INFO_REQUESTED},
    KYCState.MORE_INFO_REQUESTED: {KYCState.SUBMITTED},
    KYCState.APPROVED: set(),
    KYCState.REJECTED: set(),
}


def ensure_valid_transition(current_state: str, next_state: str) -> None:
    allowed = LEGAL_TRANSITIONS.get(current_state, set())
    if next_state not in allowed:
        raise ValueError(f"Illegal transition from {current_state} to {next_state}.")
