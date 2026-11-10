"""Domain error codes and canonical error envelopes per Section 30.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class FailureCode(str, Enum):
    INPUT_UNIT_MISMATCH = "INPUT_UNIT_MISMATCH"
    EVIDENCE_SPAN_INVALID = "EVIDENCE_SPAN_INVALID"
    ENTITY_AMBIGUOUS = "ENTITY_AMBIGUOUS"
    DATA_STALE = "DATA_STALE"
    DATA_MISSING = "DATA_MISSING"
    CALIBRATION_INSUFFICIENT = "CALIBRATION_INSUFFICIENT"
    DEPENDENCE_REPAIR_EXCEEDED = "DEPENDENCE_REPAIR_EXCEEDED"
    NONFINITE_RESULT = "NONFINITE_RESULT"
    DB_OWNER_CONFLICT = "DB_OWNER_CONFLICT"
    RUN_LEASE_EXPIRED = "RUN_LEASE_EXPIRED"
    ARTIFACT_HASH_MISMATCH = "ARTIFACT_HASH_MISMATCH"
    PROVIDER_SCHEMA_FAILED = "PROVIDER_SCHEMA_FAILED"
    MINSKY_UNAVAILABLE = "MINSKY_UNAVAILABLE"
    MINSKY_OUTPUT_INVALID = "MINSKY_OUTPUT_INVALID"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    DISK_LOW = "DISK_LOW"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: FailureCode
    message: str
    retryable: bool
    request_id: Optional[str] = None
    fields: tuple[str, ...] = ()


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    error: ErrorDetail


class ContagionDomainException(Exception):
    def __init__(
        self,
        code: FailureCode,
        message: str,
        retryable: bool = False,
        request_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
        status_code: int = 422,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.request_id = request_id
        self.fields = tuple(fields or [])
        self.status_code = status_code

    def to_envelope(self) -> ErrorEnvelope:
        return ErrorEnvelope(
            error=ErrorDetail(
                code=self.code,
                message=self.message,
                retryable=self.retryable,
                request_id=self.request_id,
                fields=self.fields,
            )
        )
