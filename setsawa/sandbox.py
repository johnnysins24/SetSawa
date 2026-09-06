"""Process resource controls; not an OS-level privilege/security boundary."""
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def windows_job(process):
    from ctypes import wintypes as w

    class BASIC(ctypes.Structure):
        _fields_ = [("user", ctypes.c_int64), ("job_user", ctypes.c_int64), ("flags", w.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t), ("active", w.DWORD), ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]

    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("ro", "wo", "oo", "rb", "wb", "ob")]

    class EXTENDED(ctypes.Structure):
        _fields_ = [("basic", BASIC), ("io", IO), ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = EXTENDED()
    limits.basic.flags = 0x2000 | 0x100  # kill on close and per-process memory
    limits.process_memory = 1024**3
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(handle, w.HANDLE(process._handle)):
        kernel.CloseHandle(handle)
        raise ctypes.WinError(ctypes.get_last_error())
    return lambda: kernel.CloseHandle(handle)


def parse_pdf(path, timeout=90):
    path = Path(path).resolve(strict=True)
    worker = Path(__file__).with_name("pdf_worker.py")
    with tempfile.TemporaryDirectory(prefix="setsawa-parser-") as tmp:
        env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
        env.update({"TEMP": tmp, "TMP": tmp, "TMPDIR": tmp, "HOME": tmp, "USERPROFILE": tmp})
        output, errors = Path(tmp) / "result.json", Path(tmp) / "error.txt"
        with output.open("wb") as out, errors.open("wb") as err:
            proc = subprocess.Popen([sys.executable, "-I", "-X", "utf8", str(worker), str(path)], cwd=tmp, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err)
            close_job = lambda: None
            try:
                if os.name == "nt":
                    close_job = windows_job(proc)
                proc.stdin.write(b"GO\n")
                proc.stdin.close()
                start = time.monotonic()
                while proc.poll() is None:
                    if time.monotonic() - start > timeout or output.stat().st_size > 32 * 1024**2 or errors.stat().st_size > 1024**2:
                        raise ValueError("PDF worker exceeded time/output limit")
                    time.sleep(0.05)
                if proc.returncode:
                    raise ValueError("PDF rejected: " + errors.read_text(encoding="utf-8", errors="replace")[:1000])
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
                close_job()
        if output.stat().st_size > 32 * 1024**2:
            raise ValueError("PDF output exceeds limit")
        return json.loads(output.read_text(encoding="utf-8"))
