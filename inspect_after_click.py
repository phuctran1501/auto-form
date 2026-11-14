import asyncio
from playwright.async_api import async_playwright

async def inspect_after_click():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = 'https://docs.google.com/forms/d/e/1FAIpQLSe8OrzsQIgvpg5WiN4U6HoLk8qarpXt5qp08sgVB81QLaNCrQ/viewform'
        await page.goto(url, wait_until='domcontentloaded')

        # Fast forward pages 1 to 7
        for _ in range(7):
            for inp in await page.locator('input[type="text"]').all():
                await inp.fill('Thử nghiệm')
            for rg in await page.locator('div[role="radiogroup"]').all():
                await rg.locator('div[role="radio"]').first.click()
            await page.locator('div[role="button"]:has-text("Tiếp")').first.click()
            await page.wait_for_timeout(1000)

        # On Page 8
        for rg in await page.locator('div[role="radiogroup"]').all():
            await rg.locator('div[role="radio"]').first.click()
        await page.wait_for_timeout(500)

        # Find submit button
        submit_btn = page.locator('div[role="button"][jsname="M2UYVd"]')
        print('Found submit button:', await submit_btn.count())

        # Screenshot before submit
        await page.screenshot(path='logs/screenshots/p8_before_submit.png')

        # Click
        await submit_btn.first.click()
        await page.wait_for_timeout(3000)

        # Screenshot after submit
        await page.screenshot(path='logs/screenshots/p8_after_submit.png')
        print('Current URL:', page.url)
        print('Page title:', await page.title())
        body = await page.inner_text('body')
        print('Body lines count:', len(body.split('\n')))
        for line in body.split('\n')[:15]:
            if line.strip():
                print('BODY LINE:', line.strip())

        await browser.close()

asyncio.run(inspect_after_click())

