from dataclasses import dataclass
from typing import List

from sqlalchemy import text


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
            text(
                """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND discipline = 'CASE_MANAGER' AND active = true
            LIMIT 1
            """
            ),
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="CASE_MANAGER", user_id=cm))

    # Assigned RN
    rn = (
        db.execute(
            text(
                """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND discipline = 'RN' AND active = true
            LIMIT 1
            """
            ),
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="RN", user_id=rn))

    # Assigned LVN
    lvn = (
        db.execute(
            text(
                """
            SELECT user_id
            FROM patient_assignments
            WHERE patient_id = :pid AND discipline = 'LVN' AND active = true
            LIMIT 1
            """
            ),
            {"pid": patient_id},
        )
        .scalar()
    )
    recipients.append(NotificationRecipient(role="LVN", user_id=lvn))

    return recipients