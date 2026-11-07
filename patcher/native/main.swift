import Cocoa
import WebKit

// Thin native shell: shows the offline patcher page and routes its "download" to a save dialog.
final class App: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate, WKScriptMessageHandlerWithReply {
    var win: NSWindow!
    var web: WKWebView!
    var savedTo: URL?

    func applicationDidFinishLaunching(_ n: Notification) {
        let cfg = WKWebViewConfiguration()
        cfg.mediaTypesRequiringUserActionForPlayback = []      // the intro tune may start when the window opens
        cfg.userContentController.addScriptMessageHandler(self, contentWorld: .page, name: "fetchOS")
        web = WKWebView(frame: .zero, configuration: cfg)
        web.navigationDelegate = self; web.uiDelegate = self
        win = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1100, height: 820),
                       styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        win.title = "DAVEY MPC PATCHER"; win.contentView = web; win.center(); win.makeKeyAndOrderFront(nil)
        let page = Bundle.main.url(forResource: "patcher", withExtension: "html")!
        web.loadFileURL(page, allowingReadAccessTo: page.deletingLastPathComponent())
        NSApp.activate(ignoringOtherApps: true)
    }
    // Akai's original OS: the page asks for the zip, we fetch it from Akai's CDN into memory (nothing is written to disk, so nothing is left to delete).
    // DAVEY_OS_URL replaces the address for tests (any URL, including file://).
    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage, replyHandler: @escaping (Any?, String?) -> Void) {
        let env = ProcessInfo.processInfo.environment["DAVEY_OS_URL"]
        guard let u = URL(string: env ?? (m.body as? String ?? "")), env != nil || (u.scheme == "https" && u.host == "cdn.inmusicbrands.com") else { replyHandler(nil, "bad url"); return }
        URLSession.shared.dataTask(with: URLRequest(url: u, timeoutInterval: 60)) { d, r, e in
            DispatchQueue.main.async {
                if let d = d, e == nil, (r as? HTTPURLResponse)?.statusCode ?? 200 == 200 { replyHandler(d.base64EncodedString(), nil) } else { replyHandler(nil, e?.localizedDescription ?? "download failed") }
            }
        }.resume()
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ a: NSApplication) -> Bool { true }

    // downloads (blob: links from the page)
    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, preferences: WKWebpagePreferences,
                 decisionHandler: @escaping (WKNavigationActionPolicy, WKWebpagePreferences) -> Void) {
        decisionHandler(a.shouldPerformDownload ? .download : .allow, preferences)
    }
    func webView(_ w: WKWebView, decidePolicyFor r: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(r.canShowMIMEType ? .allow : .download)
    }
    func webView(_ w: WKWebView, navigationAction: WKNavigationAction, didBecome d: WKDownload) { d.delegate = self }
    func webView(_ w: WKWebView, navigationResponse: WKNavigationResponse, didBecome d: WKDownload) { d.delegate = self }
    func download(_ d: WKDownload, decideDestinationUsing r: URLResponse, suggestedFilename: String,
                  completionHandler: @escaping (URL?) -> Void) {
        let p = NSSavePanel(); p.nameFieldStringValue = suggestedFilename
        p.begin { resp in self.savedTo = resp == .OK ? p.url : nil; completionHandler(self.savedTo) }
    }
    // The MPC update code reads Akai's version marker from the OS file's TIME stamp and refuses times before 01:14
    // ("OS version too old", units with a 16-bit flash chip). A file saved between 00:00 and 01:13 gets 01:14 today.
    func downloadDidFinish(_ d: WKDownload) {
        guard let u = savedTo else { return }
        let cal = Calendar.current, now = Date(), c = cal.dateComponents([.hour, .minute], from: now)
        if (c.hour ?? 0) * 60 + (c.minute ?? 0) < 74, let safe = cal.date(bySettingHour: 1, minute: 14, second: 0, of: now) {
            try? FileManager.default.setAttributes([.modificationDate: safe], ofItemAtPath: u.path)
        }
    }
    // file chooser (<input type=file>)
    func webView(_ w: WKWebView, runOpenPanelWith p: WKOpenPanelParameters, initiatedByFrame f: WKFrameInfo,
                 completionHandler: @escaping ([URL]?) -> Void) {
        let o = NSOpenPanel(); o.allowsMultipleSelection = p.allowsMultipleSelection
        o.begin { completionHandler($0 == .OK ? o.urls : nil) }
    }
    // alert/confirm from the page
    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert(); a.messageText = m; a.runModal(); completionHandler()
    }
    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert(); a.messageText = m; a.addButton(withTitle: "OK"); a.addButton(withTitle: "Cancel")
        completionHandler(a.runModal() == .alertFirstButtonReturn)
    }
}
let app = NSApplication.shared; let d = App(); app.delegate = d; app.setActivationPolicy(.regular); app.run()
