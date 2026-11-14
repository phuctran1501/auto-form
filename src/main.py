"""Main CLI entrypoint for running the auto-form batch submissions."""

import asyncio
import json
import random
import sys
from datetime import datetime
from pathlib import Path

from src.config.settings import settings
from src.filler.engine import FormFillerEngine
from src.parser.models import ProgressState, StudentRecord
from src.parser.validator import ValidationError, validate_student_record
from src.utils.logger import logger


def load_or_init_state(state_file: Path, total: int) -> ProgressState:
    """Load existing progress state or create a fresh one."""
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ProgressState(**data)
        except Exception as e:
            logger.warning("failed_to_load_state_reinitializing", error=str(e))

    return ProgressState(total_records=total)


def save_state(state_file: Path, state: ProgressState) -> None:
    """Persist current progress to state file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state.last_updated = datetime.now().isoformat()
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)


async def main(limit: int | None = None, dry_run: bool = False) -> None:
    """Run batch auto-fill process."""
    logger.info("starting_auto_form_process", dry_run=dry_run, limit=limit)

    samples_file = settings.samples_file_path
    if not samples_file.exists():
        logger.error("samples_file_not_found", path=str(samples_file))
        sys.exit(1)

    with open(samples_file, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    records: list[StudentRecord] = [StudentRecord(**r) for r in raw_records]
    total_count = len(records)
    logger.info("loaded_records_count", total=total_count)

    state = load_or_init_state(settings.state_file_path, total_count)
    completed_set = set(state.completed_indices)
    completed_mssvs = set(state.completed_mssvs)

    engine = FormFillerEngine(
        form_url=settings.form_url,
        headless=settings.headless,
        screenshots_dir=settings.screenshots_dir,
    )

    processed_in_this_run = 0

    for idx, record in enumerate(records):
        if idx in completed_set:
            continue

        if limit and processed_in_this_run >= limit:
            logger.info("run_limit_reached", limit=limit)
            break

        # Validate record
        try:
            validate_student_record(record, existing_mssvs=completed_mssvs)
        except ValidationError as e:
            logger.error("record_validation_error_skipping", index=idx, mssv=record.mssv, error=str(e))
            state.failed_indices.append(idx)
            save_state(settings.state_file_path, state)
            continue

        logger.info(
            "processing_record_item",
            index=idx + 1,
            total=total_count,
            mssv=record.mssv,
            name=record.full_name,
        )

        if dry_run:
            logger.info("dry_run_simulated_success", mssv=record.mssv)
            success = True
        else:
            success = await engine.submit_record(record)

        if success:
            state.completed_indices.append(idx)
            state.completed_mssvs.append(record.mssv)
            completed_mssvs.add(record.mssv)
            processed_in_this_run += 1
            save_state(settings.state_file_path, state)

            # Random delay 5 - 8 minutes (except for the last record or in dry_run)
            is_last = (idx == total_count - 1) or (limit and processed_in_this_run >= limit)
            if not is_last and not dry_run:
                delay = random.randint(settings.delay_min_seconds, settings.delay_max_seconds)
                logger.info(
                    "waiting_next_submission_interval",
                    delay_seconds=delay,
                    delay_minutes=round(delay / 60, 2),
                )
                await asyncio.sleep(delay)
        else:
            state.failed_indices.append(idx)
            save_state(settings.state_file_path, state)
            logger.warning("record_failed_will_retry_or_skip", mssv=record.mssv)
            # Short wait on failure
            if not dry_run:
                await asyncio.sleep(10)

    logger.info(
        "auto_form_batch_finished",
        total=total_count,
        completed=len(state.completed_indices),
        failed=len(state.failed_indices),
    )


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    limit_val = None
    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit_val = int(arg.split("=")[1])
    asyncio.run(main(limit=limit_val, dry_run=is_dry))
