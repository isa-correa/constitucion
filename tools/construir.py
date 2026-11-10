"""Genera los archivos de data/ a partir de tools/preguntas.json (que sale de tools/extraer.py).
Uso: python3 tools/construir.py"""
import json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from marcas import marca_de

# Erratas de la página antigua que se corrigen al construir.
ERRATAS = [("es la Administración legislativa ordinaria la que fija", "es el legislador ordinario quien fija")]

# Procedencia: las oficiales del C1 (INAP) y, aparte, las de Constitución de exámenes de otras administraciones.


def r(a, b):
    return set(range(a, b + 1))


# Cada tema es un acordeón y un archivo de datos. Cada bloque dice de qué asunto sale y, si hace falta, qué artículos o qué ley.
TEMAS = [
    ("tema1", "Tema 1 · La Constitución Española de 1978", [
        ("t1-preliminar", "Estructura, Preámbulo y Título Preliminar (arts. 1 a 9)", "constitucion", None),
        ("t1-derechos", "Derechos y deberes fundamentales (arts. 10 a 52)", "derechos", lambda a, c: not a & {53}),
        ("t1-garantias", "Garantías de los derechos (art. 53)", "derechos", None),
        ("t1-suspension", "Suspensión de derechos y estados excepcionales (arts. 55 y 116)", "suspension", None),
        ("t1-defensor", "El Defensor del Pueblo (art. 54 y LO 3/1981)", "defensor", None),
        ("t1-tc", "El Tribunal Constitucional (Título IX y LOTC)", "tc", None),
        ("t1-reforma", "La reforma de la Constitución (Título X)", "reforma", None),
    ]),
    ("tema2", "Tema 2 · La Corona", [
        ("t2-sucesion", "Sucesión, regencia y tutela (arts. 57 a 60)", "corona", lambda a, c: bool(a & r(57, 60)) and not a & r(61, 65)),
        ("t2-rey", "El Rey: estatuto, funciones y refrendo (arts. 56 y 61 a 65)", "corona", None),
    ]),
    ("tema3", "Tema 3 · Las Cortes Generales", [
        ("t3-composicion", "Composición, estatuto y funcionamiento (arts. 66 a 80)", "cortes", lambda a, c: bool(a) and min(a) <= 80 and "Reglamento" not in c),
        ("t3-leyes", "Elaboración de las leyes (arts. 81 a 92)", "cortes", lambda a, c: bool(a) and min(a) <= 92 and "Reglamento" not in c),
        ("t3-tratados", "Tratados internacionales (arts. 93 a 96)", "cortes", lambda a, c: bool(a) and min(a) <= 96 and "Reglamento" not in c),
        ("t3-control", "Relaciones con el Gobierno y Reglamento del Congreso", "cortes", None),
    ]),
    ("tema4", "Tema 4 · El Poder Judicial", [
        ("t4-ce", "El Poder Judicial en la Constitución (arts. 117 a 127)", "judicial", lambda a, c: "LOPJ" not in c),
        ("t4-lopj", "Ley Orgánica del Poder Judicial", "judicial", None),
    ]),
    ("tema5", "Tema 5 · El Gobierno y la Administración", [
        ("t5-ce", "El Gobierno en la Constitución (arts. 97 a 116)", "gobierno", lambda a, c: "Ley 50/1997" not in c),
        ("t5-ley", "Ley 50/1997, del Gobierno", "gobierno", None),
    ]),
    ("tema6", "Economía, Hacienda y organización territorial", [
        ("t6-economia", "Economía y Hacienda (Título VII)", "economia", None),
        ("t6-territorial", "Organización territorial del Estado (Título VIII)", "territorial", None),
    ]),
]


def articulos(p):
    """Artículos de la Constitución que citan sus preceptos (o, si no hay, su enunciado)."""
    s = set()
    for c in p["citas"]:
        f = c["fuente"].split("·")[0] if "·" in c["fuente"] and "CE" not in c["fuente"].split("·")[0] else c["fuente"]
        if re.search(r"\bCE\b", c["fuente"]):
            s |= {int(n) for n in re.findall(r"(?<![\d.])(\d{1,3})(?:\.\d+)?", f) if 1 <= int(n) <= 169}
    if not s:
        s |= {int(n) for n in re.findall(r"art(?:ículo|\.)\s*(\d{1,3})[^.:]{0,25}?(?:CE\b|Constituci)", p["enunciado"]) if 1 <= int(n) <= 169}
    return s


def origen(p):
    return "oficiales" if p["oficial"] else "otras"


def principal(p):
    """La fuente que se enseña: la oficial si la hay; si no, la primera."""
    for f in p["fuentes"]:
        if f[0].startswith("INAP"):
            return f
    return p["fuentes"][0]


def limpiar(t):
    for a, b in ERRATAS:
        t = t.replace(a, b)
    # Sin rayas: los incisos entre rayas pasan a paréntesis, una raya suelta a dos puntos, un rango a "a".
    t = re.sub(r"(\d)\s*–\s*(\d)", r"\1 a \2", t)
    t = re.sub(r"\s*[—–]\s*([^—–]+?)\s*[—–](?=\s|[.,;:)»])", r" (\1)", t)
    t = re.sub(r"\s*[—–]\s*", ": ", t)
    return t


def construir():
    fuente = json.load(open(os.path.join(AQUI, "preguntas.json"), encoding="utf-8"))
    por_tema = {t[0]: [] for t in TEMAS}
    for p in fuente:
        arts = articulos(p)
        citas = " ".join(c["fuente"] for c in p["citas"])
        tema = bloque = None
        for tid, _, bloques in TEMAS:
            for bid, _, asunto, cond in bloques:
                if p["asunto"] == asunto and (cond is None or cond(arts, citas)):
                    tema, bloque = tid, bid
                    break
            if tema:
                break
        assert tema, p["pid"]
        test, n = principal(p)
        q = {
            "id": "ce-%03d" % int(p["pid"][1:]),
            "origen": origen(p),
            "test": test,
            "n": n,
            "enunciado": limpiar(p["enunciado"]),
            "opciones": [limpiar(o) for o in p["opciones"]],
            "bloque": bloque,
            "precepto": "; ".join(c["fuente"] for c in p["citas"]) or "Constitución Española",
            "correcta": p["correcta"],
            "justificaciones": [limpiar(j) for j in p["justificaciones"]],
            "arts": sorted(arts),
        }
        if p["citas"]:
            q["citas"] = [{"texto": limpiar(c["texto"]), "fuente": limpiar(c["fuente"])} for c in p["citas"]]
        m = marca_de(arts, citas)
        if m:
            q["marca"] = m
        if p.get("ojo"):
            q["ojo"] = limpiar(p["ojo"])
        if p.get("truco"):
            q["truco"] = limpiar(p["truco"])
        por_tema[tema].append(q)

    de = {}  # Constitución no tiene supuestos: ningún tema lleva casos.
    escritos = []
    for tid, nombre, bloques in TEMAS:
        datos = {"id": tid, "nombre": nombre, "bloques": [{"id": b[0], "nombre": b[1]} for b in bloques],
                 "calendarios": {}, "casos": de.get(tid, []), "preguntas": por_tema[tid]}
        escribir(tid, datos)
        escritos.append((tid, len(por_tema[tid])))
    total = sum(n for _, n in escritos)
    marcadas = sum(1 for t in por_tema.values() for q in t if q.get("marca"))
    print("Escrito:", ", ".join("%s (%d)" % x for x in escritos), )
    print(total, "preguntas,", marcadas, "con marca")
    for tid, _, bloques in TEMAS:
        for b in bloques:
            print("  ", b[0], sum(1 for q in por_tema[tid] if q["bloque"] == b[0]))


def escribir(nombre, datos):
    ruta = os.path.join(RAIZ, "data", nombre + ".js")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("window.BANCO = window.BANCO || [];\nwindow.BANCO.push(" + json.dumps(datos, ensure_ascii=False) + ");\n")


if __name__ == "__main__":
    construir()
