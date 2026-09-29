# Edição do Reels

Resultado: `../reels_editado_HD.mp4` (1080x1920, 24 fps, H.264 + AAC, ~62 s).

1. `python3 render_base.py entrada.mp4 base.mp4` corta os silêncios e a fala repetida, alterna o zoom entre os cortes, faz o upscale para 1080x1920 e trata o áudio.
2. `python3 render_overlay.py base.mp4 final.mp4` gera as legendas palavra por palavra, os cards explicativos animados e a barra de progresso.

A transcrição revisada e os tempos de cada fala estão em `segments.py`. Para mudar um texto, altere lá e rode a etapa 2 de novo.
Dependências: ffmpeg, Pillow, fontes Montserrat e Noto Color Emoji.
