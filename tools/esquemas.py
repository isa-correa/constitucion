"""Pasa los esquemas de tools/nuevos/*.png a WebP (img/esquemas) y escribe data/esquemas.js:
APUNTES (bloques del temario), ESQUEMAS (catálogo) y ESQ_PREG (qué esquemas abre cada pregunta).
Uso: python3 tools/nuevos/generar.py && python3 tools/esquemas.py   (hace falta Pillow)."""
import json, os, re
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ANCHO = 2400

# id -> (título, artículos de la Constitución que cubre, leyes que cubre)
ESQ = {
    "estructura": ("Estructura de la Constitución", "", []),
    "historia": ("Eje cronológico: de 1978 a las cuatro reformas", "13,49,69,135", []),
    "mayorias": ("Qué mayoría pide cada cosa", "", []),
    "cifras-clave": ("Las cifras que más caen", "", []),
    "preliminar": ("Título Preliminar, arts. 1 a 9", "1-9", []),
    "valores-1": ("El artículo 1 en un mapa", "1", []),
    "titulo-1": ("Título I: capítulos y secciones, arts. 10 a 55", "10,14", []),
    "extranjeros-13": ("Españoles y extranjeros, arts. 11 a 13", "11-13,19,23", []),
    "garantias-53": ("Garantías de los derechos, art. 53", "53", []),
    "estados-116": ("Alarma, excepción y sitio, art. 116", "116", []),
    "suspension-55": ("Suspensión de derechos, art. 55", "55", []),
    "defensor-54": ("El Defensor del Pueblo, art. 54 y LO 3/1981", "54", ["LO 3/1981"]),
    "tc-159": ("Composición del Tribunal Constitucional, arts. 159 y 160", "159,160", ["LOTC"]),
    "tc-recursos": ("Qué conoce el TC y quién recurre, arts. 161 a 165", "161-165", ["LOTC"]),
    "reforma-167": ("Reforma ordinaria y agravada, arts. 166 a 169", "166-169", []),
    "sucesion-57": ("Orden de sucesión a la Corona, art. 57", "57", []),
    "regencia-59": ("Regencia y tutela, arts. 59 y 60", "59,60", []),
    "funciones-62": ("Funciones del Rey, art. 62", "56,61,62,63", []),
    "refrendo-64": ("El refrendo, arts. 64 y 65", "56,64,65", []),
    "cortes-66": ("Congreso y Senado, arts. 66 a 69", "66-80", ["Reglamento del Congreso"]),
    "senado-69": ("Cuántos senadores elige cada uno, art. 69", "69", []),
    "fuentes-81": ("Las normas con rango de ley, arts. 81 a 86", "81", []),
    "delegacion-82": ("Legislación delegada, arts. 82 a 85", "82-85", []),
    "decreto-ley-86": ("El decreto-ley, art. 86", "86", []),
    "legislativo-90": ("Cómo se hace una ley, arts. 87 a 91", "88-91", []),
    "iniciativa-87": ("Iniciativa legislativa, art. 87", "87,92", []),
    "tratados-93": ("Tratados internacionales, arts. 93 a 96", "93-96", []),
    "judicial-117": ("Principios del Poder Judicial, arts. 117 a 127", "117-121,125-127", []),
    "cgpj-122": ("El Consejo General del Poder Judicial, art. 122", "122-124", []),
    "tribunales": ("Juzgados y tribunales (LOPJ)", "123", ["LOPJ"]),
    "gobierno-98": ("Composición del Gobierno, art. 98 y Ley 50/1997", "97,98,100", ["Ley 50/1997"]),
    "investidura-99": ("La investidura, art. 99", "99", []),
    "confianza-112": ("Cuestión de confianza y moción de censura, arts. 112 a 115", "108-115", []),
    "cese-101": ("Cese y Gobierno en funciones, art. 101", "101,102", ["Ley 50/1997"]),
    "normas-gobierno": ("Jerarquía de las normas del Gobierno (Ley 50/1997)", "97", ["Ley 50/1997"]),
    "administracion-103": ("La Administración Pública, arts. 103 a 107", "103-107", []),
    "territorial-137": ("Organización territorial del Estado, arts. 137 a 142", "137-142", []),
    "acceso-143": ("Las dos vías hacia la autonomía, arts. 143 y 151", "143-147,151,152", []),
    "competencias-148": ("Competencias del Estado y de las Comunidades, arts. 148 a 150", "148-150,155", []),
    "hacienda-134": ("Los Presupuestos Generales del Estado, arts. 128 a 136", "128-136", []),
}

APUNTES = [
    {"id": "00", "nombre": "Mapas generales", "desc": "La estructura, la historia, las mayorías y las cifras. Para empezar y para repasar.",
     "grupos": [{"nombre": None, "ids": ["estructura", "historia", "mayorias", "cifras-clave"]}]},
    {"id": "01", "nombre": "Tema 1 · La Constitución Española de 1978", "desc": "Título Preliminar, derechos y garantías, Defensor del Pueblo, Tribunal Constitucional y reforma.",
     "grupos": [{"nombre": "Título Preliminar", "ids": ["preliminar", "valores-1"]},
                {"nombre": "Derechos, garantías y suspensión", "ids": ["titulo-1", "extranjeros-13", "garantias-53", "suspension-55", "estados-116", "defensor-54"]},
                {"nombre": "Tribunal Constitucional y reforma", "ids": ["tc-159", "tc-recursos", "reforma-167"]}]},
    {"id": "02", "nombre": "Tema 2 · La Corona", "desc": "Arts. 56 a 65. Sucesión, regencia, funciones del Rey y refrendo.",
     "grupos": [{"nombre": None, "ids": ["sucesion-57", "regencia-59", "funciones-62", "refrendo-64"]}]},
    {"id": "03", "nombre": "Tema 3 · Las Cortes Generales", "desc": "Arts. 66 a 96. Las Cámaras, las fuentes, el procedimiento legislativo y los tratados.",
     "grupos": [{"nombre": None, "ids": ["cortes-66", "senado-69", "fuentes-81", "delegacion-82", "decreto-ley-86", "iniciativa-87", "legislativo-90", "tratados-93"]}]},
    {"id": "04", "nombre": "Tema 4 · El Poder Judicial", "desc": "Arts. 117 a 127 y LOPJ. Principios, CGPJ y organización de los tribunales.",
     "grupos": [{"nombre": None, "ids": ["judicial-117", "cgpj-122", "tribunales"]}]},
    {"id": "05", "nombre": "Tema 5 · El Gobierno y la Administración", "desc": "Arts. 97 a 116 y Ley 50/1997. Composición, investidura, control y cese.",
     "grupos": [{"nombre": None, "ids": ["gobierno-98", "investidura-99", "confianza-112", "cese-101", "normas-gobierno", "administracion-103"]}]},
    {"id": "06", "nombre": "Economía, Hacienda y organización territorial", "desc": "Títulos VII y VIII. Presupuestos, autonomías y competencias.",
     "grupos": [{"nombre": None, "ids": ["hacienda-134", "territorial-137", "acceso-143", "competencias-148"]}]},
]

# Reglas por contenido para los esquemas generales.
GENERALES = [
    (re.compile(r"mayoría (absoluta|simple)|tres quintos|3/5|dos tercios|2/3", re.I), "mayorias"),
    (re.compile(r"cuántos títulos|estructur|Título (Preliminar|I|II|III|IV|V|VI|VII|VIII|IX|X)\b.*(regula|compren)", re.I), "estructura"),
    (re.compile(r"Preámbulo|1978.*(aprob|ratific|sancion)|reformad", re.I), "historia"),
]


def arts_de(spec):
    r = set()
    for parte in filter(None, spec.split(",")):
        a, _, b = parte.partition("-")
        r |= set(range(int(a), int(b or a) + 1))
    return r


def convertir(eid):
    png = os.path.join(AQUI, "nuevos", eid + ".png")
    salida = os.path.join(RAIZ, "img", "esquemas")
    os.makedirs(salida, exist_ok=True)
    img = Image.open(png).convert("RGB")
    if img.width != ANCHO:
        img = img.resize((ANCHO, round(img.height * ANCHO / img.width)), Image.LANCZOS)
    archivo = "%s-1.webp" % eid
    img.save(os.path.join(salida, archivo), "WEBP", quality=86, method=6)
    return {"src": "img/esquemas/" + archivo, "w": img.width, "h": img.height}


def preguntas():
    todas = []
    for f in sorted(os.listdir(os.path.join(RAIZ, "data"))):
        if f.startswith("tema"):
            t = open(os.path.join(RAIZ, "data", f), encoding="utf-8").read()
            todas += json.loads(t[t.index("push(") + 5:t.rindex(")")])["preguntas"]
    return todas


def main():
    catalogo = {}
    for eid, (titulo, spec, _) in ESQ.items():
        catalogo[eid] = {"titulo": titulo, "paginas": [convertir(eid)], "a": spec.replace("-", "-")}
    usados = {i for b in APUNTES for g in b["grupos"] for i in g["ids"]}
    assert usados == set(ESQ), set(ESQ) ^ usados
    por_preg = {}
    for p in preguntas():
        arts = set(p.get("arts", []))
        texto = p["precepto"] + " " + p["enunciado"]
        cand = []
        for eid, (_, spec, leyes) in ESQ.items():
            cubre = arts_de(spec)
            if arts & cubre or any(l in p["precepto"] for l in leyes):
                cand.append((len(cubre) or 999, eid))  # primero los más concretos
        ids = [e for _, e in sorted(cand)]
        for patron, eid in GENERALES:
            if patron.search(texto) and eid not in ids:
                ids.append(eid)
        if ids:
            por_preg[p["id"]] = ids[:4]
    with open(os.path.join(RAIZ, "data", "esquemas.js"), "w", encoding="utf-8") as f:
        f.write("window.APUNTES = " + json.dumps(APUNTES, ensure_ascii=False) + ";\n")
        f.write("window.ESQUEMAS = " + json.dumps(catalogo, ensure_ascii=False) + ";\n")
        f.write("window.ESQ_PREG = " + json.dumps(por_preg, ensure_ascii=False) + ";\n")
    print(len(catalogo), "esquemas ·", len(por_preg), "preguntas con apuntes de", len(preguntas()))


if __name__ == "__main__":
    main()
