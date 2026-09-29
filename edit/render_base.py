"""Etapa 1: corta os silêncios, alterna zoom entre cortes, faz upscale p/ 1080x1920
e trata o áudio. Uso: python3 render_base.py entrada.mp4 base.mp4"""
import subprocess
import sys

from segments import keep_segments

src, out = sys.argv[1], sys.argv[2]
segs = keep_segments()
W, H = 1080, 1920
FACE_Y = 0.42  # centro vertical aproximado do rosto (zoom ancorado aqui)

# upscale + limpeza aplicados uma vez, antes de dividir
f = [
    f"[0:v]fps=24,scale={W + 8}:{H}:flags=lanczos,crop={W}:{H},"
    "hqdn3d=1.5:1.2:4:4,unsharp=5:5:0.7:5:5:0.0,"
    f"eq=contrast=1.05:saturation=1.12:brightness=0.01,split={len(segs)}"
    + "".join(f"[v{i}]" for i in range(len(segs))),
    "[0:a]highpass=f=80,lowpass=f=12000,"
    "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
    f"asplit={len(segs)}" + "".join(f"[a{i}]" for i in range(len(segs))),
]
cat = []
for i, (a, b) in enumerate(segs):
    z = 1.0 if i % 2 == 0 else 1.12
    zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    x, y = (zw - W) // 2, int((zh - H) * FACE_Y)
    f.append(
        f"[v{i}]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,"
        f"scale={zw}:{zh}:flags=lanczos,crop={W}:{H}:{x}:{y},setsar=1[vv{i}]"
    )
    d = b - a
    f.append(
        f"[a{i}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d=0.015,afade=t=out:st={d - 0.02:.3f}:d=0.02[aa{i}]"
    )
    cat.append(f"[vv{i}][aa{i}]")
f.append("".join(cat) + f"concat=n={len(segs)}:v=1:a=1[vc][ac]")
f.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[ao]")

subprocess.run(
    ["ffmpeg", "-v", "error", "-stats", "-y", "-i", src,
     "-filter_complex", ";".join(f), "-map", "[vc]", "-map", "[ao]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", out],
    check=True,
)
print("segmentos:", len(segs), "duração:", round(sum(b - a for a, b in segs), 2))
