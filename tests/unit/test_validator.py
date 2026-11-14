"""Unit tests for student dataset generator and validator."""

import pytest

from src.generator.dataset import generate_dataset
from src.parser.models import StudentRecord
from src.parser.validator import ValidationError, validate_student_record


def test_generate_dataset_count_and_uniqueness():
    """Verify dataset generates exactly requested count with zero duplicate MSSVs."""
    count = 50
    records = generate_dataset(count=count)
    assert len(records) == count

    mssvs = [r.mssv for r in records]
    assert len(set(mssvs)) == count
    assert "B2306882" not in mssvs


def test_validate_student_record_success():
    """Verify valid record passes constraint validation."""
    record = StudentRecord(
        full_name="Nguyễn Văn An",
        gender="Nam",
        mssv="B2303844",
        major_cohort="Kinh tế - K49",
        birth_year=2005,
        hometown="Cần Thơ",
        ethnicity="Kinh",
        used_tiktok_shop="Đã từng",
        monthly_spending="Từ 2tr - 4tr",
        ratings={},
    )
    validate_student_record(record, existing_mssvs=set())


def test_validate_student_record_invalid_mssv_prefix():
    """Verify record with invalid MSSV cohort prefix is rejected."""
    record = StudentRecord(
        full_name="Nguyễn Văn An",
        gender="Nam",
        mssv="B2601234",  # K52 not allowed
        major_cohort="Kinh tế - K52",
        birth_year=2008,
        hometown="Cần Thơ",
        ethnicity="Kinh",
        used_tiktok_shop="Đã từng",
        monthly_spending="Từ 2tr - 4tr",
        ratings={},
    )
    with pytest.raises(ValidationError, match="MSSV format invalid"):
        validate_student_record(record, existing_mssvs=set())


def test_validate_student_record_author_mssv_rejected():
    """Verify form author MSSV is strictly rejected."""
    record = StudentRecord(
        full_name="Phan Vương Ái Thư",
        gender="Nữ",
        mssv="B2306882",
        major_cohort="Kinh tế - K49",
        birth_year=2005,
        hometown="Cần Thơ",
        ethnicity="Kinh",
        used_tiktok_shop="Đã từng",
        monthly_spending="Từ 2tr - 4tr",
        ratings={},
    )
    with pytest.raises(ValidationError, match="matches form author"):
        validate_student_record(record, existing_mssvs=set())


def test_validate_student_record_invalid_hometown():
    """Verify old province not in 34 reorganized list is rejected."""
    record = StudentRecord(
        full_name="Nguyễn Văn An",
        gender="Nam",
        mssv="B2301234",
        major_cohort="Kinh tế - K49",
        birth_year=2005,
        hometown="Tỉnh Cũ Không Tồn Tại",
        ethnicity="Kinh",
        used_tiktok_shop="Đã từng",
        monthly_spending="Từ 2tr - 4tr",
        ratings={},
    )
    with pytest.raises(ValidationError, match="not in 34 reorganized"):
        validate_student_record(record, existing_mssvs=set())
