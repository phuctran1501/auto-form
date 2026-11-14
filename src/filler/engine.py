"""Playwright-based Google Form automation filler supporting multi-page flows."""

import asyncio
import random
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.parser.models import StudentRecord
from src.utils.logger import logger

NEXT_BUTTON_SELECTOR = 'div[role="button"]:has-text("Tiếp"), div[role="button"]:has-text("Next")'
SUBMIT_BUTTON_SELECTOR = 'div[role="button"]:has(span:has-text("Gửi")), div[role="button"]:has(span:has-text("Gửi")), div[role="button"]:has(span:has-text("Submit"))'


class FormFillerEngine:
    """Handles end-to-end multi-page form navigation, typing, and submission."""

    def __init__(self, form_url: str, headless: bool = True, screenshots_dir: Path | None = None) -> None:
        self.form_url = form_url
        self.headless = headless
        self.screenshots_dir = screenshots_dir or Path("logs/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def _type_with_jitter(self, input_locator: Any, text: str) -> None:
        """Type text character by character with human-like jitter."""
        await input_locator.click()
        await input_locator.fill("")
        for char in str(text):
            await input_locator.press_sequentially(char)
            await asyncio.sleep(random.uniform(0.02, 0.05))

    async def _fill_short_text_by_item(self, item_locator: Any, value: str) -> None:
        """Fill short text input inside a question item."""
        inp = item_locator.locator('input[type="text"], textarea')
        await self._type_with_jitter(inp.first, value)

    async def _fill_radio(self, page: Page, entry_id: str, option_value: str) -> None:
        """Select a radio option within the item container."""
        container = page.locator(f'div[data-params*="{entry_id}"]')
        radio = container.locator(f'div[role="radio"][data-value="{option_value}"], div[role="radio"][aria-label="{option_value}"]')
        if await radio.count() == 0:
            radio = container.locator(f'label:has-text("{option_value}")')
        await radio.first.click()
        await asyncio.sleep(random.uniform(0.15, 0.3))

    async def _fill_all_page_radiogroups(self, page: Page, ratings_pool: list[int]) -> None:
        """Fill all Likert radiogroups on the current page with scores."""
        groups = await page.locator('div[role="radiogroup"]').all()
        for i, group in enumerate(groups):
            score = ratings_pool[i] if i < len(ratings_pool) else random.choice([3, 4, 5])
            radio_idx = max(0, min(score - 1, 4))
            radios = group.locator('div[role="radio"]')
            await radios.nth(radio_idx).click()
            await asyncio.sleep(random.uniform(0.1, 0.25))

    async def _click_next(self, page: Page) -> None:
        """Click Next button and wait for next section to render."""
        next_btn = page.locator(NEXT_BUTTON_SELECTOR)
        await next_btn.first.click()
        await page.wait_for_timeout(1500)

    async def submit_record(self, record: StudentRecord) -> bool:
        """Fill and submit a single student record through all 8 pages."""
        logger.info("submitting_record_start", mssv=record.mssv, name=record.full_name)

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context: BrowserContext = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page: Page = await context.new_page()

            try:
                await page.goto(self.form_url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1.5, 2.5))

                # === PAGE 1: Welcome & Overview ===
                logger.info("navigating_page", page_index=1, title="Giới thiệu")
                await self._click_next(page)

                # === PAGE 2: Personal Info (Text inputs via listitem headings) ===
                logger.info("navigating_page", page_index=2, title="Thông tin cá nhân")
                items = page.locator('div[role="listitem"]')
                await self._fill_short_text_by_item(items.nth(1), record.full_name)
                await self._fill_short_text_by_item(items.nth(2), record.mssv)
                await self._fill_short_text_by_item(items.nth(3), record.major_cohort)
                await self._fill_short_text_by_item(items.nth(4), str(record.birth_year))
                await self._fill_short_text_by_item(items.nth(5), record.hometown)
                await self._fill_short_text_by_item(items.nth(6), record.ethnicity)
                await self._click_next(page)

                # === PAGE 3: Screening (Gender, TikTok, Spending) ===
                logger.info("navigating_page", page_index=3, title="Sàng lọc & Chi tiêu")
                await self._fill_radio(page, "865109221", record.gender)
                await self._fill_radio(page, "1944629147", record.used_tiktok_shop)
                await self._fill_radio(page, "1744368170", record.monthly_spending)
                await self._click_next(page)

                # === PAGE 4: Factors 1 & 2 (Giá 3 + Thu nhập 3) ===
                p4_ids = ["367715589", "1793328063", "1337519800", "1030502833", "177287632", "358871458"]
                p4_scores = [record.ratings.get(k, 4) for k in p4_ids]
                logger.info("navigating_page", page_index=4, title="1. Giá & 2. Thu nhập")
                await self._fill_all_page_radiogroups(page, p4_scores)
                await self._click_next(page)

                # === PAGE 5: Factors 3 & 4 (Khuyến mãi 3 + Vận chuyển 3) ===
                p5_ids = ["1089747739", "547226249", "1374128538", "1047777526", "270245976", "1441213877"]
                p5_scores = [record.ratings.get(k, 4) for k in p5_ids]
                logger.info("navigating_page", page_index=5, title="3. Khuyến mãi & 4. Vận chuyển")
                await self._fill_all_page_radiogroups(page, p5_scores)
                await self._click_next(page)

                # === PAGE 6: Factors 5 & 6 (Đánh giá 4 + Livestream 3) ===
                p6_ids = ["134724748", "2054430395", "954541224", "569463304", "1186068398", "1327855885", "1860421887"]
                p6_scores = [record.ratings.get(k, 4) for k in p6_ids]
                logger.info("navigating_page", page_index=6, title="5. Đánh giá & 6. Livestream")
                await self._fill_all_page_radiogroups(page, p6_scores)
                await self._click_next(page)

                # === PAGE 7: Factors 7, 8, 9 (KOL 3 + Xu hướng 3 + Tiện lợi 3) ===
                p7_ids = ["1687227123", "1913589656", "255915353", "760325758", "212279939", "529176916", "1595323384", "422015240", "1154756447"]
                p7_scores = [record.ratings.get(k, 4) for k in p7_ids]
                logger.info("navigating_page", page_index=7, title="7. KOL, 8. Xu hướng, 9. Tiện lợi")
                await self._fill_all_page_radiogroups(page, p7_scores)
                await self._click_next(page)

                # === PAGE 8: Section 3 (Quyết định mua sắm 3 & Submit) ===
                p8_ids = ["219384669", "1261613827", "753938464"]
                p8_scores = [record.ratings.get(k, 4) for k in p8_ids]
                logger.info("navigating_page", page_index=8, title="Phần 3: Quyết định mua sắm & Submit")
                await self._fill_all_page_radiogroups(page, p8_scores)

                await asyncio.sleep(random.uniform(1.2, 2.0))

                # Click Submit button
                submit_btn = page.locator(SUBMIT_BUTTON_SELECTOR)
                await submit_btn.first.click()

                # Verify confirmation: Google form redirects to /formResponse or displays thank-you message
                try:
                    await page.wait_for_url("**/formResponse*", timeout=20000)
                except Exception:
                    await page.wait_for_selector('text="Xin chân thành cảm ơn"', timeout=10000)

                logger.info("submitting_record_success", mssv=record.mssv)
                return True

            except Exception as exc:
                screenshot_file = self.screenshots_dir / f"fail_{record.mssv}.png"
                await page.screenshot(path=str(screenshot_file), full_page=True)
                logger.error(
                    "submitting_record_failed",
                    mssv=record.mssv,
                    error=str(exc),
                    screenshot=str(screenshot_file),
                )
                return False

            finally:
                await context.close()
                await browser.close()
