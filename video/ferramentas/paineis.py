#!/usr/bin/env python3
"""Ilustrações animadas (1080x960) para tela dividida. Uso: paineis.py FONTES_DIR SAIDA_DIR [--quadros]"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FD, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
W, H, SS, FPS = 1080, 960, 2, 30
NAVY, NAVY2 = (11, 31, 58), (22, 52, 92)
GOLD, WHITE, GREY, RED = (212, 175, 55), (255, 255, 255), (150, 165, 190), (226, 72, 72)


def font(sz, black=True):
    return ImageFont.truetype(str(FD / ("Montserrat-Black.ttf" if black else "Montserrat-ExtraBold.ttf")), sz * SS)


def bg():
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(NAVY, NAVY2)) + (255,))
    d.rectangle([0, 0, W, 7], fill=GOLD + (255,))
    return im


class Layer:
    """Elemento desenhado em 2x, com entrada animada (sobe + aparece)."""
    def __init__(self, t, draw_fn):
        self.t = t
        big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(big), big)
        self.im = big.resize((W, H), Image.LANCZOS)


def S(*v):
    return [x * SS for x in v]


def texto(d, xy, s, sz, cor=WHITE, black=True, anchor="mm"):
    d.text(S(*xy), s, font=font(sz, black), fill=cor, anchor=anchor)


def titulo(s, y=95, sz=64, cor=GOLD):
    return lambda d, im: texto(d, (W / 2, y), s, sz, cor)


# ------------------------------------------------------------------ ícones
def termometro(cx, cy):
    def f(d, im):
        d.rounded_rectangle(S(cx - 26, cy - 150, cx + 26, cy + 40), radius=26 * SS, outline=WHITE, width=10 * SS)
        d.ellipse(S(cx - 55, cy + 10, cx + 55, cy + 120), fill=RED, outline=WHITE, width=10 * SS)
        d.rectangle(S(cx - 12, cy - 90, cx + 12, cy + 40), fill=RED)
        for i in range(4):
            d.line(S(cx + 40, cy - 130 + i * 35, cx + 70, cy - 130 + i * 35), fill=WHITE, width=6 * SS)
    return f


def som(cx, cy):
    def f(d, im):
        d.polygon(S(cx - 110, cy - 40, cx - 60, cy - 40, cx, cy - 100, cx, cy + 100, cx - 60, cy + 40, cx - 110, cy + 40), fill=WHITE)
        for i, r in enumerate((50, 90, 130)):
            d.arc(S(cx - r + 10, cy - r, cx + r + 10, cy + r), -45, 45, fill=GOLD, width=12 * SS)
    return f


def frasco(cx, cy):
    def f(d, im):
        pts = S(cx - 30, cy - 130, cx + 30, cy - 130, cx + 30, cy - 50, cx + 110, cy + 110, cx - 110, cy + 110, cx - 30, cy - 50)
        d.polygon(S(cx - 72, cy + 40, cx + 72, cy + 40, cx + 110, cy + 110, cx - 110, cy + 110), fill=(80, 200, 120))
        d.line(pts + pts[:2], fill=WHITE, width=10 * SS, joint="curve")
        for bx, by, r in ((-20, 0, 12), (25, -30, 9), (0, -70, 7)):
            d.ellipse(S(cx + bx - r, cy + by - r, cx + bx + r, cy + by + r), outline=WHITE, width=5 * SS)
    return f


def card(x0, y0, x1, y1, borda=GOLD):
    return lambda d, im: d.rounded_rectangle(S(x0, y0, x1, y1), radius=36 * SS, fill=(255, 255, 255, 18),
                                             outline=borda, width=5 * SS)


def icone_rotulo(cx, cy, icone, rot, meia=160, sz=40):
    def f(d, im):
        card(cx - meia, cy - 230, cx + meia, cy + 200)(d, im)
        icone(cx, cy - 40)(d, im)
        texto(d, (cx, cy + 150), rot, sz)
    return f


def holerite(d, im):
    x0, y0, x1, y1 = 250, 190, 830, 900
    d.rounded_rectangle(S(x0, y0, x1, y1), radius=20 * SS, fill=WHITE)
    texto(d, ((x0 + x1) / 2, y0 + 60), "HOLERITE", 52, NAVY)
    d.line(S(x0 + 40, y0 + 110, x1 - 40, y0 + 110), fill=NAVY, width=5 * SS)
    for i in range(4):
        y = y0 + 160 + i * 80
        d.rounded_rectangle(S(x0 + 40, y, x0 + 300, y + 30), radius=10 * SS, fill=(205, 212, 225))
        d.rounded_rectangle(S(x1 - 170, y, x1 - 40, y + 30), radius=10 * SS, fill=(205, 212, 225))
    y = y0 + 500
    d.rounded_rectangle(S(x0 + 25, y - 30, x1 - 25, y + 90), radius=16 * SS, outline=RED, width=7 * SS)
    texto(d, (x0 + 45, y + 30), "ADIC. INSALUBRIDADE", 31, NAVY, anchor="lm")
    texto(d, (x1 - 40, y + 30), "?", 64, RED, anchor="rm")


def holerite_badge(d, im):
    d.ellipse(S(730, 150, 910, 330), fill=RED, outline=WHITE, width=8 * SS)
    texto(d, (820, 243), "NÃO TEM", 30)


def barras(vals):
    def mk(i, v):
        def f(d, im):
            base, hmax, larg = 840, 520, 190
            cx = 230 + i * 310
            h = hmax * v / 40
            d.rounded_rectangle(S(cx - larg / 2, base - h, cx + larg / 2, base), radius=22 * SS,
                                fill=GOLD if v == 40 else (190, 160, 70))
            texto(d, (cx, base - h - 55), f"{v}%", 70)
        return f
    return [mk(i, v) for i, v in enumerate(vals)]


def balao(d, im):
    d.rounded_rectangle(S(90, 170, 990, 430), radius=50 * SS, fill=WHITE)
    d.polygon(S(200, 425, 280, 425, 180, 500), fill=WHITE)
    texto(d, (540, 240), "EMPRESA:", 40, RED)
    texto(d, (540, 310), "“NÃO PAGO PORQUE", 50, NAVY)
    texto(d, (540, 375), "VOCÊ JÁ TEM EPI”", 50, NAVY)


def capacete(cx, cy):
    def f(d, im):
        d.pieslice(S(cx - 110, cy - 110, cx + 110, cy + 110), 180, 360, fill=(240, 200, 40))
        d.rounded_rectangle(S(cx - 140, cy - 8, cx + 140, cy + 22), radius=12 * SS, fill=(240, 200, 40))
        d.rectangle(S(cx - 15, cy - 110, cx + 15, cy - 5), fill=(210, 170, 20))
    return f


def abafador(cx, cy):
    def f(d, im):
        d.arc(S(cx - 100, cy - 140, cx + 100, cy + 60), 180, 360, fill=WHITE, width=16 * SS)
        for s in (-1, 1):
            d.rounded_rectangle(S(cx + s * 100 - 38, cy - 50, cx + s * 100 + 38, cy + 70), radius=30 * SS, fill=RED)
    return f


def mascara(cx, cy):
    def f(d, im):
        d.rounded_rectangle(S(cx - 90, cy - 70, cx + 90, cy + 60), radius=60 * SS, fill=(200, 210, 225))
        for s in (-1, 1):
            d.ellipse(S(cx + s * 95 - 45, cy - 5, cx + s * 95 + 45, cy + 85), fill=(90, 110, 140), outline=WHITE, width=5 * SS)
        d.line(S(cx - 90, cy - 40, cx - 150, cy - 90), fill=WHITE, width=6 * SS)
        d.line(S(cx + 90, cy - 40, cx + 150, cy - 90), fill=WHITE, width=6 * SS)
    return f


def check_item(y, s, ok=True):
    def f(d, im):
        d.rounded_rectangle(S(80, y - 70, 1000, y + 70), radius=30 * SS, fill=(255, 255, 255, 22), outline=GOLD, width=4 * SS)
        d.ellipse(S(115, y - 45, 205, y + 45), fill=(60, 180, 100) if ok else RED)
        if ok:
            d.line(S(135, y, 155, y + 22, 188, y - 22), fill=WHITE, width=11 * SS, joint="curve")
        texto(d, (240, y), s, 46, anchor="lm")
    return f


def lupa(cx, cy):
    def f(d, im):
        d.ellipse(S(cx - 110, cy - 110, cx + 70, cy + 70), outline=GOLD, width=22 * SS)
        d.line(S(cx + 50, cy + 50, cx + 150, cy + 150), fill=GOLD, width=34 * SS)
        d.ellipse(S(cx - 75, cy - 75, cx + 35, cy + 35), fill=(255, 255, 255, 30))
    return f


def chip(cx, cy, s):
    def f(d, im):
        d.rounded_rectangle(S(cx - 190, cy - 85, cx + 190, cy + 85), radius=40 * SS, fill=GOLD)
        texto(d, (cx, cy), s, 76, NAVY)
    return f


def prancheta(cx, cy):
    def f(d, im):
        d.rounded_rectangle(S(cx - 95, cy - 120, cx + 95, cy + 130), radius=16 * SS, fill=(170, 120, 70))
        d.rectangle(S(cx - 75, cy - 95, cx + 75, cy + 110), fill=WHITE)
        d.rounded_rectangle(S(cx - 40, cy - 135, cx + 40, cy - 95), radius=10 * SS, fill=GREY)
        for i in range(4):
            d.line(S(cx - 55, cy - 50 + i * 40, cx + 55, cy - 50 + i * 40), fill=GREY, width=8 * SS)
    return f


def camera(cx, cy):
    def f(d, im):
        d.rounded_rectangle(S(cx - 130, cy - 70, cx + 130, cy + 100), radius=26 * SS, fill=WHITE)
        d.rounded_rectangle(S(cx - 50, cy - 105, cx + 40, cy - 60), radius=10 * SS, fill=WHITE)
        d.ellipse(S(cx - 62, cy - 47, cx + 62, cy + 77), fill=NAVY, outline=GOLD, width=10 * SS)
        d.ellipse(S(cx - 25, cy - 10, cx + 25, cy + 40), fill=(60, 90, 140))
    return f


def calendario(cx, cy):
    def f(d, im):
        d.rounded_rectangle(S(cx - 150, cy - 140, cx + 150, cy + 150), radius=26 * SS, fill=WHITE)
        d.rounded_rectangle(S(cx - 150, cy - 140, cx + 150, cy - 60), radius=26 * SS, fill=RED)
        d.rectangle(S(cx - 150, cy - 90, cx + 150, cy - 60), fill=RED)
        for s in (-1, 1):
            d.rounded_rectangle(S(cx + s * 80 - 12, cy - 170, cx + s * 80 + 12, cy - 115), radius=8 * SS, fill=GREY)
        texto(d, (cx, cy + 30), "2", 150, NAVY)
        texto(d, (cx, cy + 115), "ANOS", 40, NAVY)
    return f


# ------------------------------------------------------------------ painéis
# tempos dos elementos são relativos ao início do painel (s)
PAINEIS = {
    "A": (2.0, 6.9, [
        (0.0, titulo("VOCÊ TRABALHA COM...", sz=58)),
        (0.25, icone_rotulo(200, 520, termometro, "CALOR")),
        (0.73, icone_rotulo(540, 520, som, "BARULHO")),
        (1.29, icone_rotulo(880, 520, frasco, "QUÍMICOS")),
    ], [(2.5, [
        (0.0, holerite),
        (1.05, holerite_badge),
    ])]),
    "B": (13.3, 17.4, [(0.0, titulo("ADICIONAL DE INSALUBRIDADE", sz=50))] +
         list(zip((0.45, 0.85, 1.45), barras((10, 20, 40))))),
    "C": (23.4, 28.95, [
        (0.15, balao),
        (2.3, capacete(230, 760)),
        (2.6, abafador(540, 760)),
        (2.9, mascara(850, 760)),
    ]),
    "D": (30.5, 38.05, [
        (0.0, titulo("SÓ O EPI NÃO BASTA", sz=66)),
        (2.5, check_item(380, "NEUTRALIZAR OS RISCOS")),
        (6.0, check_item(600, "EMPRESA FISCALIZAR O USO")),
    ]),
    "E": (38.1, 44.75, [
        (0.0, titulo("QUEM DECIDE É A", sz=54, cor=WHITE)),
        (0.9, lupa(330, 470)),
        (1.0, lambda d, im: texto(d, (720, 480), "PERÍCIA", 92, GOLD)),
    ], [(3.1, [
        (0.0, titulo("SE DER POSITIVO, REFLETE NO", sz=46, cor=WHITE)),
        (0.7, chip(300, 500, "13º")),
        (1.7, chip(780, 500, "FGTS")),
    ])]),
    "F": (49.4, 56.65, [
        (0.0, titulo("GUARDE", sz=72)),
        (0.6, icone_rotulo(290, 530, prancheta, "FICHA DO EPI", 220, 40)),
        (1.7, icone_rotulo(790, 530, camera, "FOTOS DO LOCAL", 220, 40)),
    ], [(3.5, [
        (0.0, titulo("DEPOIS QUE SAIR DA EMPRESA", sz=46, cor=WHITE)),
        (1.6, calendario(540, 520)),
        (2.2, lambda d, im: texto(d, (540, 800), "PARA RECLAMAR", 50, GOLD)),
    ])]),
}


def render(nome, ini, fim, elems, fases=()):
    fase_list = [(0.0, elems)] + list(fases)
    camadas = [(t0, [Layer(t, fn) for t, fn in es]) for t0, es in fase_list]
    fundo = bg()
    n = int(round((fim - ini) * FPS))
    destino = OUT / f"{nome}.mov"
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "qtrle", str(destino)], stdin=subprocess.PIPE)
    amostras = {}
    for k in range(n):
        t = k / FPS
        fase = max(i for i, (t0, _) in enumerate(camadas) if t >= t0)
        t0, ls = camadas[fase]
        quadro = fundo.copy()
        for L in ls:
            p = (t - t0 - L.t) / 0.35
            if p <= 0:
                continue
            e = 1 - (1 - min(p, 1)) ** 3
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            tmp.paste(L.im, (0, int(40 * (1 - e))))
            if e < 1:
                a = tmp.getchannel("A").point(lambda v: int(v * e))
                tmp.putalpha(a)
            quadro.alpha_composite(tmp)
        # entrada/saída do painel (desliza de baixo / some)
        dur = fim - ini
        if t < 0.2 or t > dur - 0.15:
            k_in = min(t / 0.2, 1) if t < 0.2 else 1
            k_out = min((dur - t) / 0.15, 1) if t > dur - 0.15 else 1
            m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            m.paste(quadro, (0, int(H * (1 - k_in) * 0.25)))
            m.putalpha(m.getchannel("A").point(lambda v: int(v * min(k_in, k_out))))
            quadro = m
        proc.stdin.write(quadro.tobytes())
        if k in (int(n * 0.35), n - 10):
            amostras[k] = quadro.convert("RGB")
    proc.stdin.close()
    proc.wait()
    return destino, list(amostras.values())


if __name__ == "__main__":
    so = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set(PAINEIS)
    folha = []
    for nome, spec in PAINEIS.items():
        if nome not in so:
            continue
        ini, fim, elems = spec[:3]
        fases = spec[3] if len(spec) > 3 else ()
        dst, amos = render(nome, ini, fim, elems, fases)
        folha += amos
        print(nome, ini, fim, dst)
    th = [a.resize((W // 3, H // 3)) for a in folha]
    cols = 4
    sheet = Image.new("RGB", (cols * W // 3, ((len(th) + cols - 1) // cols) * H // 3), (0, 0, 0))
    for i, a in enumerate(th):
        sheet.paste(a, ((i % cols) * W // 3, (i // cols) * H // 3))
    sheet.save(OUT / "paineis_folha.jpg", quality=88)
