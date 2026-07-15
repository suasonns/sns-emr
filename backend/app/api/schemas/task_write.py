from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CompletionReferenceType


class TaskCompletePayload(BaseModel):
    """
    Evidence-only payload.

    Used by:
    POST /tasks/{task_id}/complete
    """

    completion_reference_type: CompletionReferenceType = Field(
        description="Type of evidence used to complete the task",
        json_schema_extra={
            "example": "VISIT"
        },
    )

    completion_reference_id: UUID = Field(
        description="UUID of the evidence record (usually a finalized visit)",
        json_schema_extra={
            "example": "4d132a34-8518-4a54-8aba-8479155495f5"
        },
    )


class TaskCompleteJSONRequest(TaskCompletePayload):
    """
    JSON-only payload.

    Used by:
    POST /tasks/complete
    """

    task_id: UUID = Field(
        description="Task UUID to complete",
        json_schema_extra={
            "example": "f7ec0ba6-839c-4aa7-95e8-49f324519f90"
        },
    )