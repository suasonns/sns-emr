from typing import List
from dataclasses import dataclass


@dataclass
class NotificationRecipient:
    role: str
    user_id: str | None


def resolve_patient_recipients(db, patient_id) -> List[NotificationRecipient]:
    """
    Compliance rule:
    - MD
    - DPCS
    - Case Manager
    - Assigned RN
    - Assigned LVN
    """

    recipients: List[NotificationRecipient] = []

    # MD (on call or attending)
    recipients.append(NotificationRecipient(role="MD", user_id=None))

    # DPCS
    recipients.append(NotificationRecipient(role="DPCS", user_id=None))

    # Case Manager (example lookup)
    cm = (
        db.execute(
            """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND role = 'CASE_MANAGER'
            LIMIT 1
            """,
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="CASE_MANAGER", user_id=cm))

    # Assigned RN
    rn = (
        db.execute(
            """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND role = 'RN'
            LIMIT 1
            """,
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="RN", user_id=rn))

    # Assigned LVN
    lvn = (
        db.execute(
            """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND role = 'LVN'
            LIMIT 1
            """,
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="LVN", user_id=lvn))

    return recipients