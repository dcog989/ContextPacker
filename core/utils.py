import platform
from pathlib import Path
import ctypes


def get_downloads_folder():
    if platform.system() == "Windows":
        from ctypes import wintypes, oledll

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]

        FOLDERID_Downloads = GUID(0x374DE290, 0x123F, 0x4565, (0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
        path_ptr = ctypes.c_wchar_p()
        oledll.ole32.CoInitialize(None)
        try:
            if oledll.shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_Downloads), 0, None, ctypes.byref(path_ptr)) == 0:
                return path_ptr.value
            else:
                raise ctypes.WinError()
        finally:
            oledll.ole32.CoTaskMemFree(path_ptr)
            oledll.ole32.CoUninitialize()
    return str(Path.home() / "Downloads")
