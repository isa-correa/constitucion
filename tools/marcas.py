"""Lo que más cae y lo que casi no cae en el test de Constitución.

Sale de cruzar dos cosas:
  1. Las listas de artículos más preguntados que publican las academias y webs de test
     (Red Opositor, Preparaoposiciones, OpoRuta, Oposapiens, josenrique.es; consultadas en noviembre de 2026).
     Coinciden casi siempre en los arts. 1, 2, 14, 53 y 168, y después en derechos fundamentales,
     estados excepcionales, Corona, fuentes del Derecho, investidura, Poder Judicial y organización territorial.
  2. Las 57 preguntas oficiales del INAP que hay en el banco (diez exámenes del C1, de 2022 a 2026).

Cada marca va atada a artículos de la Constitución (ARTS) o a una ley (LEY, que se busca en la cita).
Una pregunta recibe la marca más fuerte de las que le tocan. Tres niveles:
  estrella: aparece en casi todas las listas y además ha caído en el INAP.
  clave:    aparece en las listas o ha caído en el INAP.
  poco:     no está en ninguna lista y no ha salido en las preguntas oficiales del banco.
"""

def r(a, b):
    return set(range(a, b + 1))

MARCAS = [
    # ---------- estrella ----------
    {"nivel": "estrella", "arts": {1}, "nota": "El artículo 1 sale en casi todas las convocatorias: valores superiores, soberanía nacional y monarquía parlamentaria."},
    {"nivel": "estrella", "arts": {2}, "nota": "Unidad, autonomía y solidaridad: el artículo 2 está en todas las listas de lo más preguntado."},
    {"nivel": "estrella", "arts": {14}, "nota": "La igualdad del artículo 14 está en todas las listas. Recuerda que va con la Sección 1.ª a efectos de amparo."},
    {"nivel": "estrella", "arts": {53}, "nota": "Las garantías del artículo 53 (quién vincula, reserva de ley, amparo) están en todas las listas de lo más preguntado."},
    {"nivel": "estrella", "arts": {55, 116}, "nota": "Estados de alarma, excepción y sitio: quién los declara, cuánto duran y qué derechos se suspenden. Cae en el INAP y en todas las listas."},
    {"nivel": "estrella", "arts": {81, 86}, "nota": "Ley orgánica y decreto-ley: de lo que más se repite en el INAP (el 86 es el artículo con más preguntas oficiales del banco)."},
    {"nivel": "estrella", "arts": {99}, "nota": "La investidura del artículo 99 (plazos, mayorías y los dos meses) está en las listas y ha caído en el INAP."},
    {"nivel": "estrella", "arts": {167, 168}, "nota": "Reforma ordinaria y agravada: mayorías, referéndum y qué títulos van por el 168. En todas las listas y en el INAP."},
    # ---------- clave ----------
    {"nivel": "clave", "arts": {3, 9}, "nota": "Del Título Preliminar, tras el 1 y el 2, lo que más se repite es el 3 (lenguas) y el 9 (sujeción a la ley y los principios del 9.3)."},
    {"nivel": "clave", "arts": {13}, "nota": "Extranjeros (art. 13): el 13.2 y el voto municipal caen a menudo, también en el INAP."},
    {"nivel": "clave", "arts": {16, 17, 18, 20, 23, 24, 27}, "nota": "De la Sección 1.ª, los artículos que más repiten las listas: libertad religiosa, detención, intimidad, expresión, participación, tutela judicial y educación."},
    {"nivel": "clave", "arts": {54}, "nota": "El Defensor del Pueblo en la Constitución: alto comisionado de las Cortes, por ley orgánica."},
    {"nivel": "clave", "arts": {56, 57, 62, 64}, "nota": "De la Corona, lo que más cae: el Rey como Jefe del Estado, el orden de sucesión, sus funciones del artículo 62 y el refrendo."},
    {"nivel": "clave", "arts": {66, 68, 69}, "nota": "Composición de las Cortes, el Congreso y el Senado: cifras que el INAP pregunta a menudo."},
    {"nivel": "clave", "arts": {82, 87}, "nota": "Legislación delegada e iniciativa legislativa (las 500.000 firmas): muy repetidos en los test y en el INAP."},
    {"nivel": "clave", "arts": {93, 94}, "nota": "Tratados internacionales: qué necesita autorización por ley orgánica y cuáles solo de las Cortes. Ha caído en el INAP."},
    {"nivel": "clave", "arts": {97, 103}, "nota": "Funciones del Gobierno (art. 97) y principios de la Administración (art. 103): en las listas y en el INAP."},
    {"nivel": "clave", "arts": {113}, "nota": "La moción de censura: proponerla, votarla y qué pasa si sale."},
    {"nivel": "clave", "arts": {117, 122}, "nota": "Poder Judicial: los principios del 117 y la composición del CGPJ. Sale en todos los exámenes del INAP del banco."},
    {"nivel": "clave", "arts": {137, 143, 148, 149}, "nota": "Organización territorial y competencias (arts. 137 a 149): sube en cada convocatoria del INAP."},
    {"nivel": "clave", "arts": {159, 161, 162}, "nota": "El Tribunal Constitucional: composición, quién propone a sus doce magistrados y quién puede recurrir."},
    # ---------- poco ----------
    {"nivel": "poco", "ley": "LOTC", "nota": "El detalle de la Ley Orgánica del Tribunal Constitucional no aparece en las listas ni en las preguntas oficiales del banco."},
    {"nivel": "poco", "ley": "LOPJ", "nota": "La organización de juzgados y tribunales de la LOPJ no ha salido en las preguntas oficiales del banco."},
    {"nivel": "poco", "ley": "Reglamento del Congreso", "nota": "El Reglamento del Congreso apenas sale: una pregunta de academia en todo el banco."},
]

ORDEN = {"estrella": 0, "clave": 1, "poco": 2}


def marca_de(arts, citas):
    """arts: artículos de la Constitución de la pregunta. citas: texto de las fuentes citadas."""
    mejor = None
    for m in MARCAS:
        if "arts" in m and arts & m["arts"] or "ley" in m and m["ley"] in citas:
            if mejor is None or ORDEN[m["nivel"]] < ORDEN[mejor["nivel"]]:
                mejor = m
    return {"nivel": mejor["nivel"], "nota": mejor["nota"]} if mejor else None
