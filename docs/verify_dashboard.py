"""NEURO_PREDICT dashboard verification — viewports, themes, keyboard, overflow."""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "https://127.0.0.1:3000"
issues, console_errors = [], []

def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        issues.append(label)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 800}, color_scheme="dark")
    page = ctx.new_page()
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" and "favicon" not in m.text.lower() else None)
    page.on("pageerror", lambda e: console_errors.append(str(e)))

    page.goto(f"{BASE}/app/dashboard.html", wait_until="networkidle")
    page.wait_for_timeout(2500)  # let demo-fallback fetches settle

    # 1. Core zones rendered (demo fallback proves error→fallback path works)
    for sel, label in [
        ("#statPatients", "KPI patients value rendered"),
        ("#patientsList .list-row", "patients list rows rendered"),
        ("#activityFeed .list-row", "activity rows rendered"),
        ("#theatersList .list-row", "theaters rows rendered"),
    ]:
        check(page.locator(sel).count() > 0, label)

    # 2. No horizontal overflow at five viewports
    for w, h, name in [(320, 640, "320px"), (390, 844, "390px"), (768, 1024, "768px"), (1280, 800, "1280px"), (1920, 1080, "1920px")]:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(300)
        overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(overflow <= 0, f"no horizontal overflow at {name} (overflow={overflow}px)")

    # Screenshots: mobile + desktop
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    page.screenshot(path="docs/shots/dash-mobile-dark.png")
    page.set_viewport_size({"width": 1280, "height": 800})
    page.wait_for_timeout(400)
    page.screenshot(path="docs/shots/dash-desktop-dark.png")

    # 3. Theme toggle — icon/label change, persists, no layout explosion
    page.click("#themeToggle")
    page.wait_for_timeout(300)
    theme = page.evaluate("document.documentElement.dataset.theme")
    check(theme == "light", "theme toggles to light")
    stored = page.evaluate("localStorage.getItem('neuro_theme')")
    check(stored == "light", "theme choice persisted")
    page.screenshot(path="docs/shots/dash-desktop-light.png")
    page.click("#themeToggle")  # back to dark

    # Fresh load so keyboard tests start with no stale focus
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)

    # 4. Skip link + keyboard order
    page.keyboard.press("Tab")
    first = page.evaluate("document.activeElement.className")
    check("skip-link" in str(first), "skip link is first tab stop")
    page.keyboard.press("Enter")
    focused = page.evaluate("document.activeElement.id || document.activeElement.tagName")
    check(focused == "main-content", "skip link jumps to main content")

    # 5. Drawer: open → focus trapped → Escape restores focus
    page.set_viewport_size({"width": 768, "height": 1024})
    page.click("#mobileMenuBtn")
    page.wait_for_timeout(450)
    open_state = page.evaluate("document.querySelector('.sidebar').classList.contains('open')")
    check(open_state, "drawer opens at tablet width")
    check(page.evaluate("document.getElementById('mobileMenuBtn').getAttribute('aria-expanded')") == "true", "aria-expanded=true when open")
    for _ in range(12):
        page.keyboard.press("Tab")
    in_sidebar = page.evaluate("document.querySelector('.sidebar').contains(document.activeElement)")
    check(in_sidebar, "focus stays trapped in drawer across 12 tabs")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    check(not page.evaluate("document.querySelector('.sidebar').classList.contains('open')"), "Escape closes drawer")
    back = page.evaluate("document.activeElement.id")
    check(back == "mobileMenuBtn", "focus returns to menu button after close")

    # 6. Refresh button gives feedback + updates timestamp
    page.set_viewport_size({"width": 1280, "height": 800})
    page.click("#refreshBtn")
    page.wait_for_timeout(800)
    check("Updated" in page.locator("#updatedAt").inner_text(), "refresh updates 'Updated HH:MM' stamp")

    # 7. WCAG 1.4.4 reflow: 200% zoom ≈ half viewport + 200% root font
    page.set_viewport_size({"width": 640, "height": 400})
    page.evaluate("document.documentElement.style.fontSize = '2rem'")
    page.wait_for_timeout(400)
    overflow200 = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check(overflow200 <= 0, f"no destructive overflow at 200% zoom equivalent (overflow={overflow200}px)")
    page.evaluate("document.documentElement.style.fontSize = ''")
    page.set_viewport_size({"width": 1280, "height": 800})

    browser.close()

print(json.dumps({"issues": issues, "console_errors": console_errors[:8]}, indent=2))
sys.exit(1 if issues or console_errors else 0)
