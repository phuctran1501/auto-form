"""Data validator ensuring all constraints are strictly satisfied."""

import re

from src.generator.dataset import PROVINCES_34
from src.parser.models import StudentRecord


class ValidationError(Exception):
    """Raised when record data violates strict constraints."""


def validate_student_record(record: StudentRecord, existing_mssvs: set[str]) -> None:
    """Validate student record against all project constraints.

    Args:
        record: The student record to validate.
        existing_mssvs: Set of already submitted or duplicate MSSVs.

    Raises:
        ValidationError: If any constraint is violated.
    """
    # 1. Name validation
    if not record.full_name or len(record.full_name.split()) < 2:
        raise ValidationError(f"Invalid full name: {record.full_name}")

    # 2. MSSV format: B + 2 digits (22..25) + 5 digits (00000..08000)
    match = re.match(r"^B(22|23|24|25)(\d{5})$", record.mssv)
    if not match:
        raise ValidationError(f"MSSV format invalid: {record.mssv}")

    num_part = int(match.group(2))
    if num_part > 8000:
        raise ValidationError(f"MSSV numeric part {num_part} exceeds 08000: {record.mssv}")

    if record.mssv == "B2306882":
        raise ValidationError("MSSV matches form author B2306882!")

    if record.mssv in existing_mssvs:
        raise ValidationError(f"Duplicate MSSV detected: {record.mssv}")

    # 3. Major - Cohort format
    if " - K" not in record.major_cohort:
        raise ValidationError(f"Major-cohort format invalid: {record.major_cohort}")

    # 4. Birth year
    if not (2000 <= record.birth_year <= 2008):
        raise ValidationError(f"Birth year out of reasonable range: {record.birth_year}")

    # 5. Hometown must be in 34 provinces/cities
    if record.hometown not in PROVINCES_34:
        raise ValidationError(f"Hometown '{record.hometown}' not in 34 reorganized provinces.")

    # 6. Ethnicity
    if record.ethnicity not in {"Kinh", "Khmer", "Hoa"}:
        raise ValidationError(f"Invalid ethnicity: {record.ethnicity}")
