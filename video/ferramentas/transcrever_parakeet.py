#!/usr/bin/env python3
"""Transcrição local com sherpa-onnx (Whisper small), no formato do transcrever.py da skill.
Uso: transcrever_sherpa.py SKILL_SCRIPTS MODELO_DIR VIDEO"""
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import sherpa_onnx

sys.path.insert(0, sys.argv[1])
from video_utils import pasta_edicao, salvar_transcricao, sondar  # noqa: E402

mdir, video = Path(sys.argv[2]), Path(sys.argv[3]).resolve()
info = sondar(video)
pasta = pasta_edicao(video)
destino = pasta / f"{video.stem}.transcricao.json"

with tempfile.TemporaryDirectory() as tmp:
    wav = Path(tmp) / "a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", str(wav)], check=True)
    sil = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                          "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    with wave.open(str(wav), "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

dur = len(audio) / 16000
ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", sil)]
fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)]
# trechos de fala = complemento dos silêncios
falas, t = [], 0.0
for a, b in zip(ini, fim + [dur] * (len(ini) - len(fim))):
    if a - t > 0.15:
        falas.append([t, a])
    t = b
if dur - t > 0.15:
    falas.append([t, dur])
# agrupa trechos em blocos de até ~20 s (Whisper aceita até 30 s)
blocos = []
for a, b in falas:
    if blocos and b - blocos[-1][0] <= 20 and a - blocos[-1][1] < 1.5:
        blocos[-1][1] = b
    else:
        blocos.append([a, b])

rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=str(mdir / "encoder.int8.onnx"), decoder=str(mdir / "decoder.int8.onnx"),
    joiner=str(mdir / "joiner.int8.onnx"), tokens=str(mdir / "tokens.txt"),
    num_threads=4, model_type="nemo_transducer")

segmentos = []
for a, b in blocos:
    a0, b0 = max(0.0, a - 0.1), min(dur, b + 0.1)
    st = rec.create_stream()
    st.accept_waveform(16000, audio[int(a0 * 16000):int(b0 * 16000)])
    rec.decode_stream(st)
    r = st.result
    toks, ts = list(r.tokens), list(r.timestamps)
    pals = []
    for i, tk in enumerate(toks):
        t0 = a0 + (ts[i] if i < len(ts) else 0)
        if tk.startswith(" ") or tk.startswith("▁") or not pals:
            pals.append({"p": tk.replace("▁", "").strip(), "inicio": t0})
        else:
            pals[-1]["p"] += tk
    pals = [p for p in pals if p["p"]]
    for i, p in enumerate(pals):
        nxt = pals[i + 1]["inicio"] if i + 1 < len(pals) else b0
        p["fim"] = round(min(nxt, p["inicio"] + 1.2), 3)
        p["inicio"] = round(p["inicio"], 3)
        p["prob"] = 1.0
    if pals:
        segmentos.append({"id": len(segmentos) + 1, "inicio": pals[0]["inicio"], "fim": pals[-1]["fim"],
                          "texto": r.text.strip(), "palavras": pals})

transc = {"video": str(video), "duracao": round(info["duracao"], 3), "modelo": "parakeet-tdt-0.6b-v3 (sherpa-onnx)",
          "idioma": "pt", "segmentos": segmentos}
txt = salvar_transcricao(transc, destino)
print(f"{len(segmentos)} segmentos, {sum(len(s['palavras']) for s in segmentos)} palavras\n{txt}")
