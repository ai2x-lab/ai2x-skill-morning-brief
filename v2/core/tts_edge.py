from __future__ import annotations
import re
import subprocess
import tempfile
from pathlib import Path

EDGE_BIN = "node"
EDGE_SCRIPT = "/home/ubuntu/.npm-global/lib/node_modules/openclaw/node_modules/node-edge-tts/bin.js"


def split_chunks(text: str, max_chars: int = 120) -> list[str]:
    parts = re.split(r'([。！？；\n])', (text or '').strip())
    chunks, buf = [], ""
    for p in parts:
        if not p:
            continue
        candidate = (buf + p).strip()
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        while len(p) > max_chars:
            chunks.append(p[:max_chars])
            p = p[max_chars:]
        buf = p.strip()
    if buf:
        chunks.append(buf)
    return [c for c in chunks if c]


def synthesize(text: str, out_file: Path, voice: str = "zh-TW-HsiaoChenNeural", rate: str = "+0%", pitch: str = "+0Hz") -> Path:
    chunks = split_chunks(text)
    if not chunks:
        raise RuntimeError("empty script")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mbv2_tts_") as td:
        td = Path(td)
        part_files = []
        for i, c in enumerate(chunks, 1):
            part = td / f"part_{i:03d}.mp3"
            ok = False
            last = ""
            for _ in range(3):
                cmd = [EDGE_BIN, EDGE_SCRIPT, "--text", c, "--filepath", str(part), "--voice", voice, "--rate", rate, "--pitch", pitch, "--timeout", "60000"]
                r = subprocess.run(cmd, capture_output=True, text=True)
                last = (r.stderr or r.stdout or "")[:120]
                if part.exists() and part.stat().st_size >= 100:
                    ok = True
                    break
            if not ok:
                raise RuntimeError(f"tts failed #{i}: {last}")
            part_files.append(part)

        lst = td / "parts.txt"
        lst.write_text("".join([f"file '{p}'\n" for p in part_files]), encoding="utf-8")
        ff = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_file)], capture_output=True, text=True)
        if ff.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {ff.stderr[:160]}")

    if out_file.stat().st_size < 5000:
        raise RuntimeError("audio too small")
    return out_file
