"""Saca las preguntas de constitucion_fuente.html (la página antigua, con todo explicado)
y las deja en tools/preguntas.json con el formato de la app. Uso: python3 tools/extraer.py"""
import html, json, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(RAIZ, "constitucion_fuente.html")
SALIDA = os.path.join(RAIZ, "tools", "preguntas.json")


def texto(h):
    """HTML de un fragmento a texto con **negrita** (lo único que pinta la app)."""
    h = re.sub(r"<(b|strong)>(.*?)</\1>", r"**\2**", h, flags=re.S)
    h = re.sub(r"<br\s*/?>", " ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace("\xa0", " ")
    h = re.sub(r"\*\*\s*\*\*", "", h)
    return re.sub(r"\s+", " ", h).strip()


def fuentes(src):
    """'Test exámenes nº 2 · Test 1 nº 14 · INAP mar 2022 nº 1' -> [(test, n), ...]"""
    s = html.unescape(re.sub(r"<[^>]+>", "", src)).replace("\xa0", " ")
    s = s.replace("INAP ·", "INAP")
    r = []
    for parte in re.split(r"\s·\s", s):
        parte = re.sub(r"\s+", " ", parte).strip()
        m = re.match(r"(.*?)\s*nº\s*(.*)$", parte)
        if m:
            for n in re.findall(r"\d+", m.group(2)):
                r.append((m.group(1).strip(), int(n)))
    return r


def main():
    t = open(FUENTE, encoding="utf-8").read()
    salida = []
    for sec in re.finditer(r'<section class="cat" id="(\w+)" data-cat="\w+">(.*?)</section>', t, flags=re.S):
        asunto, cuerpo = sec.group(1), sec.group(2)
        for a in re.findall(r'<article class="q[^"]*".*?</article>', cuerpo, flags=re.S):
            pid = re.search(r'id="(p\d+)"', a).group(1)
            ok = re.search(r'data-ok="(\w)"', a).group(1)
            oficial = 'data-fuente="oficial"' in a
            opts = re.findall(r'<li class="opt[^"]*" data-k="(\w)">.*?<span class="opt-t">(.*?)</span>', a, flags=re.S)
            letras = [k for k, _ in opts]
            just = {}
            m = re.search(r'<p class="why-ok"><b>.*?</b>(.*?)</p>', a, flags=re.S)
            just[ok] = "Es esta. " + texto(m.group(1))
            for k, j in re.findall(r'<li data-ref="(\w)"><i>\w\)</i>(.*?)</li>', a, flags=re.S):
                just[k] = "No. " + texto(j)
            citas = [{"texto": texto(q), "fuente": texto(c)} for q, c in
                     re.findall(r'<blockquote class="cita">(.*?)<cite>(.*?)</cite></blockquote>', a, flags=re.S)]
            truco = re.search(r'<div class="truco"><span class="truco-l">Truco</span>(.*?)</div>', a, flags=re.S)
            ojo = re.search(r'<div class="ojo"><span class="ojo-l">Ojo</span>(.*?)</div>', a, flags=re.S)
            p = {
                "pid": pid, "asunto": asunto, "oficial": oficial,
                "fuentes": fuentes(re.search(r'<span class="q-src">(.*?)</span>', a, flags=re.S).group(1)),
                "enunciado": texto(re.search(r'<p class="stem">(.*?)</p>', a, flags=re.S).group(1)),
                "opciones": [texto(o) for _, o in opts],
                "correcta": letras.index(ok),
                "justificaciones": [just.get(k, "No.") for k in letras],
                "citas": citas,
            }
            if truco: p["truco"] = texto(truco.group(1))
            if ojo: p["ojo"] = texto(ojo.group(1))
            salida.append(p)
    json.dump(salida, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(salida), "preguntas ->", os.path.relpath(SALIDA, RAIZ))


if __name__ == "__main__":
    main()
