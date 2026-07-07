---
name: verify
description: How to headlessly render/screenshot pages in this sandbox for visual verification
---

# Headless browser verification in this sandbox

There is no X server here. Use `chromium-headless-shell`, not `chromium-shell`.

## Install (one-time per environment)

```sh
sudo apt-get install -y chromium-headless-shell
```

`chromium-shell` (apt description: "minimal shell") is a different package that is
already installed by default in this environment. **Do not use it for verification** —
it hangs forever on `--dump-dom` / `--screenshot` with no X server: it spawns
renderer processes that sit idle at 0% CPU and never exit, regardless of
`--ozone-platform=headless`, `--disable-gpu`, `--in-process-gpu`,
`dbus-run-session`, or `--disable-dev-shm-usage`. Confirmed by direct testing,
not by inference (dbus warnings are a red herring — installing/running
`dbus-daemon` does not fix it either). `chromium-headless-shell` is the
purpose-built "old headless shell" binary and just works, no extra flags,
no dbus, no Xvfb needed.

## Recipe

Dump rendered DOM:

```sh
chromium-headless-shell --disable-gpu --no-sandbox --dump-dom "http://127.0.0.1:8000/some/path" > out.html
```

Screenshot:

```sh
chromium-headless-shell --disable-gpu --no-sandbox --window-size=1280,800 \
  --screenshot=out.png "http://127.0.0.1:8000/some/path"
```

Then `Read` the resulting `out.png` (or `out.html`) to inspect it.

Both exit 0 in well under 15s once the target URL is reachable. Only harmless
stderr noise to expect: `WARNING:...vaapi_wrapper.cc...drmGetDevices2() has
not found any devices` and a sandbox-init warning — neither indicates failure.

## For this app specifically

Start the dev server first (see README/DESIGN.md for the
`DJANGO_FORCE_SCRIPT_NAME=` / `manage.py runserver` + `npm run build`/`npm run dev`
workflow), then point `chromium-headless-shell` at the served URL. Requires
logging in first for any page behind auth — either drive the login form via a
scripted POST + saved session cookie jar (`--cookie-jar`-style curl, or a
CDP session), or accept that `--dump-dom` on an auth-gated route will just
show the login form, which is still useful to confirm routing/rendering.

## Scripted interaction (login, filling forms, clicking) via Playwright + CDP

`--dump-dom`/`--screenshot` are one-shot: navigate, capture, exit. No
form-filling or clicking. For an auth-gated SPA flow (log in, then interact),
drive `chromium-headless-shell` over the Chrome DevTools Protocol with
Playwright instead of trying to inject/replay cookies (cookie DB values are
encrypted in modern Chromium and there's no `cryptography`/AES lib installed
here to fake that — don't go down that path, it's a dead end).

```sh
# One-off, no browser download (chromium-headless-shell is already the browser):
npm install -D playwright-core   # in whichever dir has node_modules; uninstall after if not kept

# Launch chromium-headless-shell with a debugging port instead of --dump-dom/--screenshot:
chromium-headless-shell --headless=new --disable-gpu --no-sandbox \
  --remote-debugging-port=9333 --user-data-dir=/tmp/some-profile-dir about:blank &
```

```js
// script.cjs (must be .cjs if the project's package.json has "type": "module")
const { chromium } = require("playwright-core");
(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9333");
  const page = await browser.contexts()[0].newPage();
  await page.goto("http://host/", { waitUntil: "networkidle" });
  await page.fill("#username", "...");
  await page.fill("#password", "...");
  await page.getByRole("button", { name: "Log in", exact: true }).click(); // see gotcha below
  await page.screenshot({ path: "out.png" });
  await browser.close();
})();
```

Run with `node script.cjs` **from the directory containing `node_modules`**
(module resolution is cwd-relative; running it from elsewhere throws
`MODULE_NOT_FOUND` even though the file itself is fine).

Gotchas hit in practice:

- **Ambiguous CSS selectors silently click the wrong element.** A generic
  `button[type="submit"]` matched a language-switcher button before it ever
  reached the real login submit button, so the click "succeeded" but nothing
  happened — no error, just a silent no-op followed by a confusing timeout
  on the expected follow-up network request. Use `page.getByRole("button",
  { name: "...", exact: true })` (accessible-name matching) instead of a CSS
  tag/attribute selector whenever more than one element could plausibly
  match.
- **The browser process accumulates open tabs/pages across script runs** if
  you keep reusing the same long-lived `chromium-headless-shell` instance
  and don't `page.close()`/`browser.close()`. After a dozen or so leftover
  pages this actually failed hard (`net::ERR_INSUFFICIENT_RESOURCES` on
  navigation). If things get flaky after many iterations, just kill and
  restart the CDP-mode chromium process rather than debugging why a query
  suddenly stalls.
- **`page.screenshot({ fullPage: true })` can visibly clip/crop content on
  the right edge when the page was opened via `connectOverCDP` on an
  already-running browser** (as opposed to a browser Playwright launched
  itself) — even though `document.documentElement.scrollWidth` correctly
  equals the viewport width (i.e. there's no real CSS overflow). Confirmed
  this is a capture artifact, not a layout bug, by re-taking the same shot
  with `fullPage` omitted (plain viewport screenshot) — it rendered
  perfectly. If a `fullPage` screenshot looks suspiciously clipped, re-check
  with a non-`fullPage` shot (and/or `document.documentElement.scrollWidth
  === window.innerWidth` via `page.evaluate`) before reporting a mobile
  layout bug.
- Native HTML5 `<input max="...">`/`required` constraints genuinely block
  form submission on a real Playwright click (the browser's own constraint
  validation intercepts it, so no network request fires at all) — this is
  correct browser behavior, not a bug, but it means testing a
  server-side-only validation path requires removing the client attribute
  first, e.g. `await someInput.evaluate((el) => el.removeAttribute("max"))`,
  before clicking submit.
