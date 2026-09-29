"""Etapa 2: desenha legendas palavra-a-palavra + cards explicativos animados e
compõe sobre o vídeo base. Uso: python3 render_overlay.py base.mp4 final.mp4"""
import math
import subprocess
import sys
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from segments import PHRASES, keep_segments, to_new

base, out = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 24
SEGS = keep_segments()
DUR = sum(b - a for a, b in SEGS)
T = lambda t: to_new(t, SEGS)  # noqa: E731

FD = "/usr/share/fonts/truetype/montserrat/"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW, WHITE, CYAN, RED, GREEN = (255, 212, 0), (255, 255, 255), (64, 200, 255), (255, 86, 86), (80, 220, 130)
PANEL = (14, 18, 32, 215)


@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(FD + f"Montserrat-{name}.ttf", size)


@lru_cache(None)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    r = size / max(im.size)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def paste_scaled(dst, im, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------------------------------------------------------- legendas
def build_words():
    words = []
    for s, e, text in PHRASES:
        toks = text.split()
        weights = [len(w.strip(",.?")) + 2 for w in toks]
        tot, acc = sum(weights), 0.0
        for w, k in zip(toks, weights):
            ws = s + (e - s) * acc / tot
            acc += k
            words.append({"w": w, "s": T(ws), "e": T(s + (e - s) * acc / tot), "end": w[-1] in ".,?"})
    return words


def build_chunks(words, max_words=3, max_chars=16):
    chunks, cur = [], []
    for wd in words:
        cur.append(wd)
        txt = " ".join(x["w"] for x in cur)
        if len(cur) >= max_words or len(txt) >= max_chars or wd["end"]:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else DUR
        c_end = min(nxt, c[-1]["e"] + 0.5)
        for wd in c:
            wd["chunk_end"] = c_end
    return chunks


KEYWORDS = {"neurociência", "córtex", "pré-frontal", "lógica", "decisões", "obras", "20,", "25",
            "amígdala", "medo", "impulsividade", "vapor.", "freio", "plástico", "adolescência,",
            "adolescência?", "habilidades,", "esportes", "idiomas", "identidade", "confusão,",
            "papéis", "neurodesenvolvimento.", "plasticidade", "cerebral", "estudos,", "intensas", "emoções"}

CAP_Y = 1330
CAP_FONT = font("Black", 84)


def draw_caption(frame, t, chunks):
    for c in chunks:
        if c[0]["s"] - 0.03 <= t < c[-1]["chunk_end"]:
            break
    else:
        return
    txt_words = [wd["w"].upper() for wd in c]
    sp = CAP_FONT.getlength(" ")
    widths = [CAP_FONT.getlength(w) for w in txt_words]
    # quebra em até 2 linhas
    lines, line, lw = [], [], 0
    for i, wdt in enumerate(widths):
        if line and lw + sp + wdt > 900:
            lines.append(line)
            line, lw = [], 0
        lw += (sp if line else 0) + wdt
        line.append(i)
    lines.append(line)
    pop = ease_back((t - c[0]["s"]) / 0.18)
    layer = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lh = 100
    y0 = 150 - lh * len(lines) / 2
    for li, idxs in enumerate(lines):
        total = sum(widths[i] for i in idxs) + sp * (len(idxs) - 1)
        x = (W - total) / 2
        for i in idxs:
            wd = c[i]
            active = wd["s"] <= t < (c[i + 1]["s"] if i + 1 < len(c) else wd["chunk_end"])
            kw = wd["w"].lower() in KEYWORDS
            col = YELLOW if active else (CYAN if kw and t >= wd["s"] else WHITE)
            if t < wd["s"]:
                col = (235, 235, 235)
            y = y0 + li * lh + lh / 2
            if active:
                bw = widths[i] + 28
                d.rounded_rectangle((x - 14, y - 50, x - 14 + bw, y + 48), 18, fill=(0, 0, 0, 120))
            d.text((x, y), txt_words[i], font=CAP_FONT, fill=col, anchor="lm",
                   stroke_width=9, stroke_fill=(0, 0, 0))
            x += widths[i] + sp
    paste_scaled(frame, layer, W / 2, CAP_Y, 0.8 + 0.2 * pop, min(1, pop * 1.5))


# ---------------------------------------------------------------- cards
def panel(w, h, accent):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w - 4, h - 4), 34, fill=PANEL, outline=accent + (255,), width=5)
    return im


def chip(text, em, color, size=40):
    f = font("ExtraBold", size)
    tw = f.getlength(text)
    e = emoji(em, int(size * 1.15)) if em else None
    w = int(tw + 58 + (e.width + 14 if e else 0)) if not e else int(14 + e.width + 14 + tw + 30)
    h = int(size * 1.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=color + (255,))
    x = 14
    if e:
        r = h / 2 - 6
        cx = x + e.width / 2 - 8
        d.ellipse((cx - r, h / 2 - r, cx + r, h / 2 + r), fill=(20, 22, 34))
        e2 = e.resize((int(e.width * 0.82), int(e.height * 0.82)), Image.LANCZOS)
        im.alpha_composite(e2, (int(cx - e2.width / 2), int((h - e2.height) / 2)))
        x += e.width + 14
    d.text((x, h / 2), text, font=f, fill=(15, 15, 25), anchor="lm")
    return im


class Card:
    """Card no topo da tela com título, ícone e elementos que entram em sequência."""
    TOP = 250  # centro vertical do card

    def __init__(self, t0, t1, title, em, accent, items=(), height=300):
        self.t0, self.t1, self.title, self.em, self.accent = t0, t1, title, em, accent
        self.items, self.h = list(items), height

    def render(self, t):
        im = panel(1000, self.h, self.accent)
        d = ImageDraw.Draw(im)
        e = emoji(self.em, 84)
        im.alpha_composite(e, (40, 34))
        d.text((150, 76), self.title, font=font("Black", 52), fill=self.accent, anchor="lm")
        for it in self.items:
            it(im, d, t)
        return im

    def draw(self, frame, t):
        if not (self.t0 <= t < self.t1):
            return
        p_in = (t - self.t0) / 0.35
        p_out = (self.t1 - t) / 0.25
        s = 0.7 + 0.3 * ease_back(p_in)
        a = min(1.0, p_in * 2, p_out)
        if p_out < 1:
            s = 0.9 + 0.1 * p_out
        img = self.render(t)
        paste_scaled(frame, img, W / 2, self.TOP + img.height / 2 - 150, s, a)


def chip_item(t_on, text, em, color, x, y, size=40):
    c = chip(text, em, color, size)

    def f(im, d, t):
        p = (t - t_on) / 0.3
        if p <= 0:
            return
        s = ease_back(p)
        sc = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.BILINEAR)
        im.alpha_composite(sc, (int(x + (c.width - sc.width) / 2), int(y + (c.height - sc.height) / 2)))
    return f


def chip_row(y, specs, size=40, gap=16, x0=60):
    """specs: [(t_on, texto, emoji, cor)] — posiciona os chips lado a lado."""
    items, x = [], x0
    for t_on, text, em, color in specs:
        items.append(chip_item(t_on, text, em, color, x, y, size))
        x += chip(text, em, color, size).width + gap
    assert x - gap <= 960, f"linha de chips larga demais: {specs}"
    return items


def text_item(t_on, text, x, y, size=40, color=WHITE, weight="Bold", anchor="la"):
    def f(im, d, t):
        p = ease_out((t - t_on) / 0.3)
        if p <= 0:
            return
        col = tuple(int(v * p + 20 * (1 - p)) for v in color)
        d.text((x, y + 20 * (1 - p)), text, font=font(weight, size), fill=col, anchor=anchor)
    return f


def bar_item(t_on, t_full, label_l, label_r, frac, color, y, marker=None):
    """Barra horizontal que enche de 0 até frac entre t_on e t_full."""
    def f(im, d, t):
        if t < t_on:
            return
        p = ease_out((t - t_on) / max(0.01, t_full - t_on)) * frac
        x0, x1 = 60, 940
        d.rounded_rectangle((x0, y, x1, y + 34), 17, fill=(255, 255, 255, 45))
        d.rounded_rectangle((x0, y, x0 + max(34, (x1 - x0) * p), y + 34), 17, fill=color + (255,))
        d.text((x0, y + 46), label_l, font=font("SemiBold", 30), fill=(200, 205, 220), anchor="la")
        d.text((x1, y + 46), label_r, font=font("SemiBold", 30), fill=(200, 205, 220), anchor="ra")
        if marker and t >= marker[0]:
            mx = x0 + (x1 - x0) * marker[1]
            q = ease_back((t - marker[0]) / 0.3)
            d.polygon([(mx, y - 6), (mx - 16 * q, y - 34 * q), (mx + 16 * q, y - 34 * q)], fill=YELLOW)
    return f


def meter_item(t_on, label, em, color, frac, y, t_len=0.6, note=None):
    e = emoji(em, 46)

    def f(im, d, t):
        if t < t_on:
            return
        p = ease_out((t - t_on) / t_len) * frac
        im.alpha_composite(e, (60, y - 4))
        d.text((125, y + 20), label, font=font("ExtraBold", 36), fill=WHITE, anchor="lm")
        x0, x1 = 420, 940
        d.rounded_rectangle((x0, y + 4, x1, y + 38), 17, fill=(255, 255, 255, 45))
        d.rounded_rectangle((x0, y + 4, x0 + max(34, (x1 - x0) * p), y + 38), 17, fill=color + (255,))
        if note:
            d.text((x1 - 14, y + 21), note, font=font("Bold", 24), fill=(15, 15, 25), anchor="rm")
    return f


P = {i: (T(s), T(e)) for i, (s, e, _) in enumerate(PHRASES)}
s_, e_ = (lambda i: P[i][0]), (lambda i: P[i][1])

cards = [
    Card(s_(0), e_(1) + 0.2, "SEU FILHO ADOLESCENTE", "🧠", YELLOW, [
        text_item(s_(0) + 0.3, "Por que as emoções são tão intensas?", 60, 150, 40),
        chip_item(s_(1), "A neurociência explica", "🔬", CYAN, 60, 215, 38),
    ], height=320),
    Card(s_(2), e_(7) + 0.3, "CÓRTEX PRÉ-FRONTAL", "🧩", CYAN, [
        *chip_row(140, [(s_(3) + 0.8, "Lógica", "💡", CYAN), (s_(4), "Decisões", "⚖️", CYAN),
                        (s_(5), "EM OBRAS", "🚧", YELLOW)], size=38),
        bar_item(s_(6), e_(7), "nascimento", "20–25 anos: maduro", 1.0, GREEN, 250,
                 marker=(s_(7), 0.99)),
    ], height=350),
    Card(s_(8) + 0.9, e_(10) + 0.3, "AMÍGDALA", "🔥", RED, [
        text_item(s_(8) + 1.2, "processa as reações emocionais", 60, 138, 36, (220, 225, 235), "SemiBold"),
        *chip_row(200, [(s_(8) + 2.2, "Medo", "😨", RED), (s_(9), "Impulsividade", "⚡", YELLOW)]),
        chip_item(s_(10) + 0.3, "A TODO VAPOR", "🚀", RED, 60, 290),
    ], height=410),
    Card(s_(11), e_(13) + 0.5, "EMOÇÃO x LÓGICA", "⚖️", YELLOW, [
        meter_item(s_(11), "Emoção", "🔥", RED, 1.0, 150, note="100%"),
        meter_item(s_(11) + 0.8, "Freio", "🧠", CYAN, 0.45, 225, t_len=1.2),
        text_item(s_(12), "O freio ainda está em calibração", 60, 300, 36, (220, 225, 235), "SemiBold"),
    ], height=380),
    Card(s_(14), e_(19) + 0.4, "PLASTICIDADE CEREBRAL", "✨", GREEN, [
        text_item(s_(15), "o cérebro se molda como nunca", 60, 138, 36, (220, 225, 235), "SemiBold"),
        text_item(s_(17) + 0.4, "Melhor fase para aprender:", 60, 200, 38, WHITE, "ExtraBold"),
        *chip_row(262, [(s_(17) + 2.2, "Habilidades", "🛠️", GREEN), (s_(18), "Esportes", "⚽", GREEN),
                        (s_(19), "Idiomas", "🌍", GREEN)], size=36, gap=12),
    ], height=400),
    Card(s_(20), e_(25) + 0.4, "IDENTIDADE x CONFUSÃO", "🎭", (190, 140, 255), [
        text_item(s_(20) + 0.2, "a grande fase do adolescente", 60, 138, 36, (220, 225, 235), "SemiBold"),
        chip_item(s_(22), "Testar novos papéis", "🎭", (200, 160, 255), 60, 200),
        *chip_row(292, [(s_(23), "Descobrir quem é", "🔍", (200, 160, 255)),
                        (s_(24) + 0.2, "É NORMAL", "✅", GREEN)]),
    ], height=410),
    Card(s_(26), e_(26) + 0.5, "FEZ SENTIDO PRA VOCÊ?", "💬", YELLOW, [
        chip_item(s_(26) + 0.5, "Comente aqui embaixo", "👇", YELLOW, 60, 150),
    ], height=260),
    Card(s_(27), DUR, "NO PRÓXIMO VÍDEO", "▶️", CYAN, [
        text_item(s_(28), "Plasticidade cerebral", 60, 138, 42, WHITE, "ExtraBold"),
        chip_item(s_(30), "Mandar bem nos estudos", "📚", CYAN, 60, 205),
        chip_item(e_(33) - 0.1, "Siga para não perder!", "🔔", YELLOW, 60, 300),
    ], height=410),
]


# ---------------------------------------------------------------- composição
def progress(frame, t):
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, W, 10), fill=(255, 255, 255, 60))
    d.rectangle((0, 0, int(W * t / DUR), 10), fill=YELLOW + (255,))


def main():
    words = build_words()
    chunks = build_chunks(words)
    n = int(round(DUR * FPS))
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-i", base,
         "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]",
         "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart",
         "-c:a", "copy", out],
        stdin=subprocess.PIPE,
    )
    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(n):
        t = i / FPS
        frame = blank.copy()
        progress(frame, t)
        for c in cards:
            c.draw(frame, t)
        draw_caption(frame, t, chunks)
        ff.stdin.write(frame.tobytes())
        if i % 240 == 0:
            print(f"{i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    if len(sys.argv) > 3:  # modo preview: renderiza só um quadro em t
        t = float(sys.argv[3])
        ch = build_chunks(build_words())
        fr = Image.open(sys.argv[1]).convert("RGBA")
        progress(fr, t)
        for c in cards:
            c.draw(fr, t)
        draw_caption(fr, t, ch)
        fr.convert("RGB").save(out)
    else:
        main()
