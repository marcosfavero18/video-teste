# Falas (tempo no vídeo ORIGINAL, em segundos) — transcrição revisada.
# O trecho 11.02–14.81 (gaguejada "que é a parte que cu... das") e o ruído em
# 61.97–62.54 foram removidos intencionalmente.
PHRASES = [
    (2.44, 7.28, "Você já se perguntou por que as emoções do seu filho parecem tão intensas na adolescência?"),
    (8.04, 9.13, "A neurociência explica."),
    (9.74, 11.02, "O córtex pré-frontal,"),
    (14.81, 16.79, "que é a parte que cuida da lógica"),
    (17.20, 18.15, "e das decisões,"),
    (18.68, 19.77, "ainda está em obras"),
    (20.19, 21.73, "e só amadurece totalmente"),
    (22.13, 24.18, "após os 20, 25 anos."),
    (24.98, 28.24, "Enquanto isso, a amígdala, que processa reações como medo"),
    (28.49, 29.37, "e impulsividade,"),
    (29.97, 31.21, "está a todo vapor."),
    (31.68, 34.38, "E o cérebro ainda não tem o freio da lógica"),
    (34.64, 36.00, "totalmente calibrado"),
    (36.19, 36.81, "para segurá-lo."),
    (38.08, 40.75, "O lado incrível é que o cérebro nunca será tão"),
    (40.95, 41.49, "plástico"),
    (41.74, 42.59, "quanto na adolescência,"),
    (43.14, 46.45, "o que faz desta a melhor época para aprender novas habilidades,"),
    (46.95, 47.34, "esportes"),
    (47.92, 49.29, "ou idiomas com facilidade."),
    (50.04, 51.67, "O adolescente está vivendo"),
    (52.03, 54.81, "a fase da identidade versus confusão,"),
    (55.37, 56.76, "onde testar novos papéis"),
    (57.10, 58.28, "e descobrir quem você é"),
    (58.79, 59.36, "faz parte"),
    (59.75, 60.88, "do neurodesenvolvimento."),
    (63.34, 64.73, "Isso que eu falei faz sentido para você?"),
    (65.34, 67.86, "Se você quiser, no próximo vídeo nós podemos falar sobre"),
    (68.05, 69.82, "como a plasticidade cerebral"),
    (70.43, 71.26, "ajuda você,"),
    (72.65, 73.60, "ajuda seu filho"),
    (73.93, 74.59, "a mandar bem"),
    (74.90, 75.50, "nos estudos,"),
    (75.92, 76.68, "se bem aproveitada."),
]

PRE, POST = 0.10, 0.14   # respiro mantido antes/depois de cada fala
MERGE_GAP = 0.20         # pausas menores que isso não são cortadas
TAIL = 0.9               # segura o final para o card de encerramento


def keep_segments():
    segs = []
    for i, (s, e, _) in enumerate(PHRASES):
        a, b = max(0.0, s - PRE), e + POST
        if i == len(PHRASES) - 1:
            b = e + TAIL
        if segs and a - segs[-1][1] < MERGE_GAP:
            segs[-1][1] = b
        else:
            segs.append([a, b])
    return segs


def to_new(t, segs):
    """Mapeia um tempo do vídeo original para a timeline editada."""
    acc = 0.0
    for a, b in segs:
        if t < a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc
