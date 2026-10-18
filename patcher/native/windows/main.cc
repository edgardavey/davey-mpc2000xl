// DAVEY MPC PATCHER for Windows: a native window (WebView2, built into Windows 10/11) showing the offline patcher page.
// Same page as the macOS app (patcher/native/main.swift). The page's download links (SAVE, report) go through a native
// Save dialog instead of a browser download. Built by build_win.py (cross-compiled with Zig; no installer, no extra DLLs).
#include "webview/webview.h"

#include <windows.h>
#include <commdlg.h>

#include <string>

#include "patcher_html.h"   // generated: const unsigned char PATCHER_HTML[] (NUL-terminated)

static std::wstring widen(const std::string &s) {
  if (s.empty()) return std::wstring();
  int n = MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), nullptr, 0);
  std::wstring w(n, L'\0');
  MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), &w[0], n);
  return w;
}

static std::string b64decode(const std::string &in) {
  static int T[256];
  static bool init = false;
  if (!init) {
    for (int i = 0; i < 256; i++) T[i] = -1;
    const char *a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for (int i = 0; i < 64; i++) T[(unsigned char)a[i]] = i;
    init = true;
  }
  std::string out;
  int val = 0, bits = -8;
  for (unsigned char c : in) {
    if (T[c] < 0) continue;            // skips '=' padding and anything unexpected
    val = (val << 6) + T[c];
    bits += 6;
    if (bits >= 0) { out.push_back(char((val >> bits) & 0xff)); bits -= 8; }
  }
  return out;
}

// Called from the page: nativeSave(fileName, base64Data) -> true when written, false when cancelled or failed.
static std::string native_save(HWND owner, const std::string &req) {
  std::string name = webview::detail::json_parse(req, "", 0);
  std::string data = b64decode(webview::detail::json_parse(req, "", 1));
  std::wstring file = widen(name);
  wchar_t path[MAX_PATH] = {0};
  wcsncpy(path, file.c_str(), MAX_PATH - 1);
  OPENFILENAMEW ofn;
  ZeroMemory(&ofn, sizeof(ofn));
  ofn.lStructSize = sizeof(ofn);
  ofn.hwndOwner = owner;
  ofn.lpstrFile = path;
  ofn.nMaxFile = MAX_PATH;
  bool txt = name.size() > 4 && (name.substr(name.size() - 4) == ".txt");
  ofn.lpstrFilter = txt ? L"Text (*.txt)\0*.txt\0All files\0*.*\0" : L"MPC OS file (*.BIN)\0*.BIN\0All files\0*.*\0";
  ofn.lpstrDefExt = txt ? L"txt" : L"BIN";
  ofn.lpstrTitle = L"Save";
  ofn.Flags = OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR;
  if (!GetSaveFileNameW(&ofn)) return "false";
  HANDLE h = CreateFileW(path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (h == INVALID_HANDLE_VALUE) return "false";
  DWORD written = 0;
  BOOL ok = WriteFile(h, data.data(), (DWORD)data.size(), &written, nullptr);
  CloseHandle(h);
  return (ok && written == data.size()) ? "true" : "false";
}

// Runs at the start of every page load: route <a download> clicks (blob: links made by the page) to nativeSave.
static const char *SAVE_HOOK = R"JS(
document.addEventListener('click', async function (e) {
  const a = e.target && e.target.closest ? e.target.closest('a[download]') : null;
  if (!a || !window.nativeSave) return;
  e.preventDefault(); e.stopPropagation();
  const buf = new Uint8Array(await (await fetch(a.href)).arrayBuffer());
  let s = '';
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
  await window.nativeSave(a.getAttribute('download'), btoa(s));
}, true);
)JS";

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
  // the intro tune may start when the window opens (as in the macOS app); arguments already set (e.g. a debug port) are kept
  std::wstring args = L"--autoplay-policy=no-user-gesture-required";
  wchar_t prev[1024];
  DWORD n = GetEnvironmentVariableW(L"WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", prev, 1024);
  if (n > 0 && n < 1024) args = std::wstring(prev) + L" " + args;
  SetEnvironmentVariableW(L"WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", args.c_str());
  try {
    webview::webview w(false, nullptr);
    w.set_title("DAVEY MPC PATCHER");
    w.set_size(1100, 820, WEBVIEW_HINT_NONE);
    HWND hwnd = (HWND)w.window().value();
    w.bind("nativeSave", [hwnd](const std::string &req) -> std::string { return native_save(hwnd, req); });
    w.init(SAVE_HOOK);
    w.set_html(reinterpret_cast<const char *>(PATCHER_HTML));
    w.run();
  } catch (const webview::exception &e) {
    MessageBoxW(nullptr,
                L"DAVEY MPC PATCHER needs the Microsoft Edge WebView2 Runtime (built into Windows 10 and 11).\n"
                L"Install it from microsoft.com/edge/webview2 and start the patcher again.",
                L"DAVEY MPC PATCHER", MB_ICONERROR);
    return 1;
  }
  return 0;
}
