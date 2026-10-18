param([int]$ProcId, [string]$Action, [string]$Path)
# Used by test_win.mjs: answers the patcher's native Save dialog with Win32 messages.
# Action save = type Path into the file name box and click Save; cancel = click Cancel. Exit 2 = no dialog, 4 = overwrite prompt.
Add-Type @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class Dlg {
  delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern int GetDlgCtrlID(IntPtr h);
  [DllImport("user32.dll")] static extern IntPtr GetDlgItem(IntPtr d, int id);
  [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, StringBuilder l);
  [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
  public static IntPtr Find(uint pid) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
      if (p == pid && IsWindowVisible(h) && Cls(h) == "#32770") { found = h; return false; } return true; }, IntPtr.Zero);
    return found;
  }
  public static string Title(IntPtr h) { var s = new StringBuilder(256); GetWindowText(h, s, 256); return s.ToString(); }
  // the file name box is Edit id 1001 (inside the file name ComboBox)
  public static IntPtr NameBox(IntPtr dlg) {
    IntPtr found = IntPtr.Zero;
    EnumChildWindows(dlg, (h, l) => { if (Cls(h) == "Edit" && GetDlgCtrlID(h) == 1001) { found = h; return false; } return true; }, IntPtr.Zero);
    return found;
  }
  public static string GetText(IntPtr h) { var s = new StringBuilder(1024); SendMessage(h, 0x000D, (IntPtr)1024, s); return s.ToString(); }
  // typed like a user (EM_SETSEL all + WM_CHAR): the dialog ignores WM_SETTEXT, it follows CBN_EDITCHANGE
  public static void Type(IntPtr h, string t) {
    SendMessage(h, 0x00B1, IntPtr.Zero, (IntPtr)(-1));
    foreach (char c in t) SendMessage(h, 0x0102, (IntPtr)c, IntPtr.Zero);
  }
  // BM_CLICK on the dialog's own button (1 = Save, 2 = Cancel), posted so the modal loop handles it like a real click
  public static void Click(IntPtr dlg, int id) { PostMessage(GetDlgItem(dlg, id), 0x00F5, IntPtr.Zero, IntPtr.Zero); }
}
'@
function WaitDialog { for ($i = 0; $i -lt 60; $i++) { $d = [Dlg]::Find($ProcId); if ($d -ne [IntPtr]::Zero) { return $d }; Start-Sleep -Milliseconds 250 }; return [IntPtr]::Zero }
$dlg = WaitDialog
if ($dlg -eq [IntPtr]::Zero) { Write-Output 'NO_DIALOG'; exit 2 }
Write-Output ('DIALOG "' + [Dlg]::Title($dlg) + '"')
if ($Action -eq 'cancel') { [Dlg]::Click($dlg, 2); Write-Output 'CANCELLED'; exit 0 }
$box = [Dlg]::NameBox($dlg)
Write-Output ('SUGGESTED "' + [Dlg]::GetText($box) + '"')
[Dlg]::Type($box, $Path)
[Dlg]::Click($dlg, 1)
Start-Sleep -Milliseconds 800
$next = [Dlg]::Find($ProcId)
if ($next -ne [IntPtr]::Zero) { Write-Output ('UNEXPECTED "' + [Dlg]::Title($next) + '": answering No'); [Dlg]::Click($next, 7); exit 4 }
Write-Output 'SAVED'
