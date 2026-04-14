document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-json]")
  if (!button) return

  const viewer = button.closest("[data-json-viewer]")
  const pre = viewer && viewer.querySelector("pre")
  if (!pre) return

  const originalLabel = button.dataset.label || button.textContent || "Copy"

  try {
    await navigator.clipboard.writeText(pre.textContent || "")
    button.textContent = button.dataset.copiedLabel || "Copied!"
  } catch (_error) {
    button.textContent = "Copy failed"
  }

  button.disabled = true
  window.setTimeout(() => {
    button.textContent = originalLabel
    button.disabled = false
  }, 1500)
})

document.addEventListener("change", (event) => {
  const field = event.target.closest("[data-autosubmit-setting]")
  if (!field || !field.form) return

  const initialValue = field.dataset.initialValue ?? ""
  const currentValue = field.value ?? ""
  if (currentValue === initialValue) return

  field.form.requestSubmit()
})

// ---------------------------------------------------------------------------
// Page loader
// Appears only after 400 ms of waiting — fast responses produce no flash.
// ---------------------------------------------------------------------------
const _LOADER_SKIP = ["/playground/settings", "/playground/request-log"]
const _LOADER_DELAY_MS = 400
let _loaderTimer = null

function _activateLoader () {
  const el = document.getElementById("page-loader")
  if (!el) return
  el.classList.add("loader-active")
  el.setAttribute("aria-hidden", "false")
}

function _scheduleLoader () {
  if (_loaderTimer !== null) return
  _loaderTimer = window.setTimeout(() => {
    _loaderTimer = null
    _activateLoader()
  }, _LOADER_DELAY_MS)
}

function _hideLoader () {
  if (_loaderTimer !== null) {
    window.clearTimeout(_loaderTimer)
    _loaderTimer = null
  }
  const el = document.getElementById("page-loader")
  if (!el) return
  el.classList.remove("loader-active")
  el.setAttribute("aria-hidden", "true")
}

// Show on form submissions that cause a full-page reload.
document.addEventListener("submit", (event) => {
  const form = event.target
  if (!form || !form.action) return
  try {
    const pathname = new URL(form.action).pathname
    if (_LOADER_SKIP.some((a) => pathname === a)) return
  } catch (_) { return }
  _scheduleLoader()
})

// Show on internal navigation link clicks (nav, tabs, Refetch, etc.).
document.addEventListener("click", (event) => {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  const link = event.target.closest("a[href]")
  if (!link) return
  const href = link.getAttribute("href")
  if (!href || href.startsWith("#") || href.startsWith("mailto:")) return
  if (link.target === "_blank") return
  try {
    const url = new URL(href, location.href)
    if (url.origin !== location.origin) return
  } catch (_) { return }
  _scheduleLoader()
})

// Remove loader if the browser restores a page from the back/forward cache.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) _hideLoader()
})

// Clear pending state if the browser keeps the page alive in the bfcache.
window.addEventListener("pagehide", _hideLoader)
