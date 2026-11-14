"""Data models for student records and form questions."""

from typing import Literal

from pydantic import BaseModel, Field


class StudentRecord(BaseModel):
    """Pydantic model representing a single student survey response."""

    full_name: str = Field(..., description="Full Vietnamese name")
    gender: Literal["Nam", "Nữ"] = Field(..., description="Gender")
    mssv: str = Field(..., pattern=r"^B\d{2}\d{5}$", description="Student ID (B + 2 digits + 5 digits)")
    major_cohort: str = Field(..., description="Format: <Major> - K<Cohort>")
    birth_year: int = Field(..., ge=2000, le=2008, description="Birth year")
    hometown: str = Field(..., description="One of 34 reorganized provinces/cities")
    ethnicity: Literal["Kinh", "Khmer", "Hoa"] = Field(..., description="Ethnicity")
    used_tiktok_shop: Literal["Đã từng", "Chưa từng"] = "Đã từng"
    monthly_spending: Literal[
        "Dưới 2tr", "Từ 2tr - 4tr", "Từ 4tr - 6tr", "Từ 6tr trở lên"
    ] = Field(..., description="Average monthly spending")

    # Likert Scale Grid fields (31 sub-items in total, scored 1 to 5)
    ratings: dict[str, int] = Field(
        default_factory=dict,
        description="Mapping from entry_id to Likert score (1..5)",
    )


class ProgressState(BaseModel):
    """Track progress across batch submissions for resuming."""

    total_records: int
    completed_indices: list[int] = Field(default_factory=list)
    completed_mssvs: list[str] = Field(default_factory=list)
    failed_indices: list[int] = Field(default_factory=list)
    last_updated: str = ""
