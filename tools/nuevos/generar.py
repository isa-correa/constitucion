"""Genera las hojas de los esquemas de Constitución (A4 apaisado, mismo estilo que los de contratos).
Uso: python3 tools/nuevos/generar.py [id ...]   (sin ids: todas). Cada hoja se pinta con Chrome a PNG.
Después, python3 tools/esquemas.py las pasa a WebP y escribe data/esquemas.js."""
import math, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
AVISO = ('<div class="aviso"><svg viewBox="0 0 24 24"><path d="M12 2 1 21h22z" fill="#c98a00"/>'
         '<path d="M12 9v6m0 2.5v.5" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></svg><span>%s</span></div>')
HOJAS = {}


def hoja(fn):
    HOJAS[fn.__name__.replace("_", "-")] = fn
    return fn


def pagina(nombre, titulo, sub, cuerpo, aviso=None):
    h = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="base.css"><link rel="stylesheet" href="ce.css">'
         '<div class="hoja"><h1>%s</h1><p class="sub">%s</p>%s%s</div>') % (titulo, sub, cuerpo, AVISO % aviso if aviso else "")
    open(os.path.join(AQUI, nombre + ".html"), "w", encoding="utf-8").write(h)


# ---------- piezas ----------
def c(txt, cls="", sub="", w=None, h=None, extra=""):
    st = []
    if w: st.append("width:%dpx" % w if isinstance(w, int) else "flex:%s" % w)
    if h: st.append("min-height:%dpx" % h)
    if extra: st.append(extra)
    s = '<div class="c %s" style="%s"><div>%s' % (cls, ";".join(st), txt)
    return s + ("<small>%s</small>" % sub if sub else "") + "</div></div>"


def t(x):
    return '<b class="t">%s</b>' % x


def fila(*piezas, cls="", gap=None, extra=""):
    st = ("gap:%dpx;" % gap if gap is not None else "") + extra
    return '<div class="fila %s" style="%s">%s</div>' % (cls, st, "".join(piezas))


FV = '<div class="flecha-v"></div>'
FH = '<div class="flecha-h"></div>'


def flujo(*filas, extra=""):
    return '<div class="stage flujo" style="%s">%s</div>' % (extra, "".join(filas))


def tabla(cab, filas, cls="m", anchos=None, extra=""):
    h = '<table class="t %s" style="%s"><tr>' % (cls, extra)
    for i, x in enumerate(cab):
        h += '<th%s>%s</th>' % (' style="width:%s"' % anchos[i] if anchos and anchos[i] else "", x)
    h += "</tr>"
    for f in filas:
        h += "<tr>" + "".join("<td%s>%s</td>" % (' class="iz"' if i and not str(x).startswith("<span") else "", x) for i, x in enumerate(f)) + "</tr>"
    return h + "</table>"


def stage(x, extra=""):
    return '<div class="stage" style="%s">%s</div>' % (extra, x)


def eje(hitos, alto=470):
    """hitos = [(posición 0..1, fecha, texto, arriba?, clase)]"""
    h = '<div class="eje" style="height:%dpx"><div class="linea"></div>' % alto
    mitad = alto // 2
    for pos, fecha, txt, arriba, cls in hitos:
        caja = '<div class="fecha">%s</div><div class="c %s" style="margin-top:6px"><div>%s</div></div>' % (fecha, cls, txt)
        if arriba:
            h += ('<div class="hito" style="left:%.1f%%;bottom:%dpx">%s<div class="marca" style="bottom:-40px;height:40px"></div></div>'
                  % (pos * 100, mitad + 40, caja))
        else:
            h += ('<div class="hito" style="left:%.1f%%;top:%dpx"><div class="marca" style="top:-40px;height:40px"></div>%s</div>'
                  % (pos * 100, mitad + 40, caja))
        h += '<div class="hito" style="left:%.1f%%;top:0;height:100%%"><div class="punto"></div></div>' % (pos * 100)
    return h + "</div>"


def mapa(centro, ramas, r=245, ancho=1027, alto=600, cw=230, ch=None, giro=0.0):
    """Mapa mental: un nodo central y ramas alrededor. ramas = [(texto, clase)]"""
    cx, cy = ancho // 2, alto // 2
    n = len(ramas)
    lineas, cajas = "", ""
    for i, (txt, cls) in enumerate(ramas):
        a = -math.pi / 2 + giro + 2 * math.pi * i / n
        x, y = cx + r * 1.62 * math.cos(a), cy + r * math.sin(a)
        x = min(max(x, cw / 2 + 4), ancho - cw / 2 - 4)
        lineas += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#374151" stroke-width="2.6"/>' % (cx, cy, x, y)
        cajas += ('<div class="c %s" style="position:absolute;left:%dpx;top:%dpx;width:%dpx;transform:translate(-50%%,-50%%)"><div>%s</div></div>'
                  % (cls, x, y, cw, txt))
    cajas += ('<div class="c q" style="position:absolute;left:%dpx;top:%dpx;width:250px;min-height:110px;transform:translate(-50%%,-50%%)"><div>%s</div></div>'
              % (cx, cy, centro))
    return ('<div class="stage" style="position:relative;height:%dpx"><svg class="lin" viewBox="0 0 %d %d">%s</svg>%s</div>'
            % (alto, ancho, alto, lineas, cajas))


def cifras(lista, cols=4):
    h = '<div class="cifras" style="grid-template-columns:repeat(%d,1fr)">' % cols
    for num, txt, cls in lista:
        h += '<div class="cifra %s"><b>%s</b><span>%s</span></div>' % (cls, num, txt)
    return h + "</div>"


def sinoptico(raiz, ramas, wr=250):
    return ('<div class="sinop"><div class="c q" style="width:%dpx;min-height:120px">%s</div><div class="llave"></div><div class="ramas">%s</div></div>'
            % (wr, raiz, "".join(ramas)))


def org(nodo, hijos=None):
    if not hijos:
        return nodo
    hs = "".join('<div class="hijo">%s</div>' % h for h in hijos)
    return '<div class="org">%s<div class="hijos%s">%s</div></div>' % (nodo, " solo" if len(hijos) == 1 else "", hs)


# ====================== 00 · Mapas generales ======================
@hoja
def estructura():
    tit = [("Preámbulo", "sin artículos", "gr"), ("Título Preliminar", "arts. 1 a 9", "az"), ("I · Derechos y deberes", "arts. 10 a 55", ""),
           ("II · La Corona", "arts. 56 a 65", ""), ("III · Las Cortes Generales", "arts. 66 a 96", ""), ("IV · Gobierno y Administración", "arts. 97 a 107", ""),
           ("V · Gobierno y Cortes", "arts. 108 a 116", ""), ("VI · Poder Judicial", "arts. 117 a 127", ""), ("VII · Economía y Hacienda", "arts. 128 a 136", ""),
           ("VIII · Organización territorial", "arts. 137 a 158", ""), ("IX · Tribunal Constitucional", "arts. 159 a 165", ""), ("X · Reforma constitucional", "arts. 166 a 169", "")]
    rej = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:6px">'
    rej += "".join(c(t(a), cls, b, h=96) for a, b, cls in tit) + "</div>"
    disp = fila(c(t("4") + " adicionales", "gr", w="1"), c(t("9") + " transitorias", "gr", w="1"), c(t("1") + " derogatoria", "gr", w="1"),
                c(t("1") + " final", "gr", w="1"), extra="margin-top:16px")
    pagina("estructura", "Estructura de la Constitución", "Preámbulo, Título Preliminar, <b>diez títulos</b> y <b>169 artículos</b>, más las disposiciones finales",
           stage(rej + disp), "<b>Truco:</b> el Título I va del 10 al 55. Los tres poderes tienen título propio: Cortes (III), Gobierno (IV) y Poder Judicial (VI).")


@hoja
def historia():
    h = eje([
        (0.07, "31 oct 1978", "Las Cortes <b>aprueban</b>", True, ""),
        (0.19, "6 dic 1978", "El pueblo <b>ratifica</b> en referéndum", False, "az"),
        (0.31, "27 dic 1978", "El Rey <b>sanciona</b> y promulga", True, ""),
        (0.43, "29 dic 1978", "<b>BOE</b> y entrada en vigor", False, "si"),
        (0.57, "1992", "Art. <b>13.2</b>: sufragio pasivo municipal (Maastricht)", True, "gr"),
        (0.69, "2011", "Art. <b>135</b>: estabilidad presupuestaria", False, "gr"),
        (0.81, "2024", "Art. <b>49</b>: personas con discapacidad", True, "gr"),
        (0.92, "2026", "Art. <b>69.3</b>: senador propio de Formentera", False, "gr"),
    ], alto=500)
    pagina("historia", "Eje cronológico de la Constitución", "Tres verbos y tres sujetos en 1978, y las <b>cuatro reformas</b> desde entonces",
           stage(h), "Las cuatro reformas se hicieron por el procedimiento <b>ordinario del 167</b>. El 168 no se ha usado nunca.")


@hoja
def mayorias():
    filas = [
        ["Simple<br><small>más sí que no</small>", "Segunda votación de investidura (99.3) · cuestión de confianza (112) · enmiendas del Senado (90.2) · levantar el veto pasados dos meses (90.2) · leyes ordinarias"],
        ["Absoluta<br><small>más de la mitad de los miembros</small>", "Primera votación de investidura (99.3) · moción de censura (113) · ley orgánica, votación final en el Congreso (81.2) · veto del Senado y levantarlo en el acto (90.2) · estado de sitio (116.4) · Senado en el 155"],
        ["Tres quintos", "Reforma ordinaria en cada Cámara (167.1) · magistrados del TC que proponen Congreso y Senado (159.1) · vocales del CGPJ que proponen las Cámaras (122.3) · Defensor del Pueblo (LO 3/1981)"],
        ["Dos tercios", "Reforma agravada, dos veces en cada Cámara (168) · Congreso en el 167.2 si el Senado dio mayoría absoluta"],
    ]
    pagina("mayorias", "Qué mayoría pide cada cosa", "Las cuatro mayorías de la Constitución, de menos a más exigente",
           stage(tabla(["Mayoría", "Dónde se pide"], filas, anchos=["230px", None])),
           "<b>Ojo:</b> la moción de censura pide mayoría <b>absoluta</b>; la cuestión de confianza, solo <b>simple</b>.")


@hoja
def cifras_clave():
    lista = [("4 años", "Mandato del Congreso y del Senado (68.4 y 69.6)", ""), ("5 años", "Defensor del Pueblo y vocales del CGPJ", ""),
             ("9 años", "Magistrados del TC; se renuevan por tercios cada 3", ""), ("3 años", "Presidente del TC (160)", ""),
             ("15 días", "Estado de alarma · sanción real de las leyes (91) · pedir referéndum en el 167.3", "a"),
             ("30 días", "Estado de excepción (más otros 30) · convalidar un decreto-ley (86.2)", "a"),
             ("2 meses", "Plazo de investidura (99.5) · el Senado para vetar o enmendar (90.2)", "a"), ("48 horas", "Segunda votación de investidura (99.3)", "a"),
             ("500.000", "Firmas de la iniciativa legislativa popular (87.3)", "v"), ("50", "Diputados o senadores para el recurso de inconstitucionalidad (162)", "v"),
             ("1/10", "Diputados para la moción de censura (113.2) · de una Cámara para el referéndum del 167", "v"), ("15 años", "De ejercicio para ser magistrado del TC o vocal jurista del CGPJ", "v"),
             ("300 a 400", "Diputados (68.1); hoy son 350", "r"), ("4", "Senadores por provincia (69.2)", "r"),
             ("3 meses", "Antes de que acaben los Presupuestos, el Gobierno presenta los nuevos (134.3)", "r"), ("20 días", "Plazo del Senado en los proyectos urgentes (90.3)", "r")]
    pagina("cifras-clave", "Las cifras que más caen", "Plazos, años, firmas y mayorías: la Constitución en dieciséis números", cifras(lista))


# ====================== 01 · Tema 1 ======================
@hoja
def preliminar():
    ramas = [c("<b>Art. 1</b> · Estado social y democrático de Derecho; valores superiores; soberanía en el pueblo; monarquía parlamentaria", "izq bl"),
             c("<b>Art. 2</b> · Unidad de la Nación, autonomía de nacionalidades y regiones, solidaridad", "izq bl"),
             c("<b>Art. 3</b> · Castellano oficial, deber de conocerlo y derecho a usarlo; las demás lenguas, oficiales en sus Comunidades", "izq bl"),
             c("<b>Art. 4</b> · Bandera roja, amarilla y roja (la amarilla, doble ancho) · <b>Art. 5</b> · Capital: Madrid", "izq bl"),
             c("<b>Art. 6</b> · Partidos políticos · <b>Art. 7</b> · Sindicatos y asociaciones empresariales", "izq bl"),
             c("<b>Art. 8</b> · Fuerzas Armadas: soberanía, independencia, integridad territorial y orden constitucional", "izq bl"),
             c("<b>Art. 9</b> · Sujeción a la Constitución; igualdad real y efectiva (9.2); los principios del <b>9.3</b>", "izq bl")]
    pagina("preliminar", "Título Preliminar", "Arts. 1 a 9: los cimientos del Estado, artículo por artículo",
           stage(sinoptico(t("Título Preliminar") + "<small>arts. 1 a 9</small>", ramas), "display:flex;align-items:center"),
           "<b>9.3</b>: legalidad, jerarquía normativa, publicidad, irretroactividad de lo sancionador no favorable, seguridad jurídica, responsabilidad e interdicción de la arbitrariedad.")


@hoja
def valores_1():
    pagina("valores-1", "El artículo 1", "Lo que más cae del Título Preliminar, en un mapa",
           mapa("<b>Art. 1</b><small>España se constituye en un Estado social y democrático de Derecho</small>", [
               ("<b>Valores superiores</b><small>libertad · justicia · igualdad · pluralismo político</small>", "az"),
               ("<b>Soberanía nacional</b><small>reside en el pueblo español, del que emanan los poderes del Estado (1.2)</small>", ""),
               ("<b>Forma política</b><small>Monarquía parlamentaria (1.3)</small>", "si"),
               ("<b>Estado social</b><small>los poderes promueven la igualdad real (9.2)</small>", "gr"),
               ("<b>Estado democrático</b><small>pluralismo político y partidos (6)</small>", "gr"),
               ("<b>Estado de Derecho</b><small>sujeción a la Constitución y a la ley (9.1)</small>", "gr")], r=215, cw=260, alto=560),
           "<b>Trampa típica:</b> son <b>cuatro</b> valores superiores. La «dignidad» o la «seguridad» no están en el 1.1.")


@hoja
def titulo_1():
    rows = [c(t("Art. 10") + "<small>dignidad de la persona; interpretación conforme a la Declaración Universal</small>", "gr", w="1"),
            c(t("Capítulo I") + "<small>Españoles y extranjeros · arts. 11 a 13</small>", "", w="1"),
            c(t("Capítulo II") + "<small>Derechos y libertades · arts. 14 a 38</small>", "az", w="1.4"),
            c(t("Capítulo III") + "<small>Principios rectores de la política social y económica · arts. 39 a 52</small>", "", w="1.2"),
            c(t("Capítulo IV") + "<small>Garantías · arts. 53 y 54</small>", "", w="1"),
            c(t("Capítulo V") + "<small>Suspensión · art. 55</small>", "", w="1")]
    sec = fila(c("<b>Art. 14</b><small>igualdad</small>", "si", w=180),
               c("<b>Sección 1.ª</b> · Derechos fundamentales y libertades públicas<small>arts. 15 a 29</small>", "si", w=360),
               c("<b>Sección 2.ª</b> · Derechos y deberes de los ciudadanos<small>arts. 30 a 38</small>", "bl", w=360), extra="margin-top:0")
    pagina("titulo-1", "Título I: derechos y deberes fundamentales", "Arts. 10 a 55: un artículo suelto y cinco capítulos",
           flujo(fila(*rows, gap=10), FV, sec),
           "El Capítulo II se parte en dos: el <b>14 y la Sección 1.ª</b> tienen la protección máxima (amparo); la Sección 2.ª, no.")


@hoja
def extranjeros_13():
    venn = ('<svg viewBox="0 0 1027 590" style="width:100%;height:100%"><g transform="translate(0,40)">'
            '<circle cx="380" cy="290" r="255" fill="#e3edfa" stroke="#1466d9" stroke-width="3" fill-opacity=".85"/>'
            '<circle cx="650" cy="290" r="255" fill="#e0f3ea" stroke="#168a5b" stroke-width="3" fill-opacity=".75"/>'
            '<text x="270" y="-14" font-size="24" font-weight="700" fill="#1466d9" text-anchor="middle">Solo españoles</text>'
            '<text x="760" y="-14" font-size="24" font-weight="700" fill="#168a5b" text-anchor="middle">Extranjeros</text>'
            '<g font-size="17" fill="#1f2937" text-anchor="middle">'
            '<text x="272" y="220">Art. 23: participar en</text><text x="272" y="246">los asuntos públicos y</text><text x="272" y="272">acceder a cargos públicos</text>'
            '<text x="272" y="332">Art. 19: elegir residencia</text><text x="272" y="358">y circular por España</text>'
            '<text x="758" y="220">Asilo, en los términos</text><text x="758" y="246">de la ley (13.4)</text>'
            '<text x="758" y="306">Extradición: por tratado</text><text x="758" y="332">o ley, con reciprocidad;</text><text x="758" y="358">nunca por delitos políticos</text><text x="758" y="384">(el terrorismo no lo es)</text></g>'
            '<g font-size="19" font-weight="700" fill="#1f2d44" text-anchor="middle"><text x="515" y="200">Los dos</text></g>'
            '<g font-size="17" fill="#1f2937" text-anchor="middle"><text x="515" y="232">Libertades públicas</text><text x="515" y="254">del Título I, según</text><text x="515" y="276">tratados y ley (13.1)</text>'
            '<text x="515" y="318" font-weight="700">Excepción 13.2:</text><text x="515" y="340">votar y ser elegido</text><text x="515" y="362">en las <tspan font-weight="700">municipales</tspan></text><text x="515" y="384">(reciprocidad)</text></g></g></svg>')
    pagina("extranjeros-13", "Españoles y extranjeros", "Arts. 11 a 13: quién tiene qué derechos", stage(venn),
           "Ningún español de origen puede ser privado de su nacionalidad (11.2). La nacionalidad se rige por <b>la ley</b> (11.1).")


@hoja
def garantias_53():
    filas = [
        ["Art. 14 y Sección 1.ª<br><small>arts. 14 a 29</small>", '<span class="s">✓</span>', '<span class="s">✓</span>', '<span class="s">✓</span>', '<span class="s">✓</span>', "Ley orgánica (81)"],
        ["Art. 30.2<br><small>objeción de conciencia</small>", '<span class="s">✓</span>', '<span class="s">✓</span>', '<span class="n">✗</span>', '<span class="s">✓</span>', "Ley"],
        ["Sección 2.ª<br><small>arts. 30 a 38</small>", '<span class="s">✓</span>', '<span class="s">✓</span>', '<span class="n">✗</span>', '<span class="n">✗</span>', "Ley que respete el contenido esencial"],
        ["Capítulo III<br><small>arts. 39 a 52</small>", '<span class="n">✗</span>', '<span class="n">✗</span>', '<span class="n">✗</span>', '<span class="n">✗</span>', "Solo alegables según las leyes que los desarrollen (53.3)"],
    ]
    cab = ["Qué derechos", "Vinculan a todos los poderes", "Recurso de inconstitucionalidad", "Procedimiento preferente y sumario", "Recurso de amparo", "Desarrollo"]
    pagina("garantias-53", "Garantías de los derechos", "Art. 53: cuánta protección tiene cada parte del Título I",
           stage(tabla(cab, filas, anchos=["210px", None, None, None, None, "220px"])),
           "<b>La pregunta estrella:</b> el amparo cubre el 14, la Sección 1.ª y la objeción de conciencia del <b>30.2</b>. Nada más.")


@hoja
def estados_116():
    filas = [["Quién lo declara", "El Gobierno, por decreto en Consejo de Ministros", "El Gobierno, por decreto en Consejo de Ministros", "El Congreso, por mayoría absoluta"],
             ["Papel del Congreso", "Se le da cuenta; sin su autorización no se prorroga", "Autorización <b>previa</b>", "Lo declara, a propuesta <b>exclusiva</b> del Gobierno"],
             ["Duración", "Hasta <b>15 días</b>", "<b>30 días</b>, prorrogables otros 30", "La que fije el Congreso"],
             ["Suspende derechos", '<span class="no">No</span>, solo limita', '<span class="si">Sí</span>, los del 55.1 (el 17.3 sí se respeta)', '<span class="si">Sí</span>, los del 55.1, incluido el 17.3']]
    pagina("estados-116", "Alarma, excepción y sitio", "Art. 116 y art. 55.1: tabla comparativa de los tres estados",
           stage(tabla(["", "Alarma", "Excepción", "Sitio"], filas, anchos=["190px", None, None, None])),
           "Durante cualquiera de los tres <b>no puede disolverse el Congreso</b>, y si está disuelto actúa su Diputación Permanente.")


@hoja
def suspension_55():
    sus = ["<b>17</b> · libertad y detención", "<b>18.2</b> · inviolabilidad del domicilio", "<b>18.3</b> · secreto de las comunicaciones",
           "<b>19</b> · residencia y circulación", "<b>20.1 a) y d)</b> y <b>20.5</b> · expresión, información y secuestro de publicaciones",
           "<b>21</b> · reunión y manifestación", "<b>28.2</b> · huelga", "<b>37.2</b> · conflicto colectivo"]
    izq = c(t("55.1 · Suspensión general") + "<small>estados de excepción y sitio</small><ul>%s</ul>" % "".join("<li>%s</li>" % x for x in sus), "izq", w="1.25")
    der = c(t("55.2 · Suspensión individual") + "<small>por ley orgánica</small><ul><li>Solo <b>17.2</b>, <b>18.2</b> y <b>18.3</b></li><li>Personas determinadas</li>"
            "<li>Investigaciones de bandas armadas o terrorismo</li><li>Con intervención judicial y control parlamentario</li></ul>", "izq am", w="1")
    pagina("suspension-55", "Suspensión de derechos", "Art. 55: qué se puede suspender, cuándo y a quién",
           flujo(fila(izq, der, gap=26)),
           "En el estado de <b>excepción</b> el 17.3 (información al detenido y abogado) <b>no</b> se suspende; en el de sitio, sí. El 16 no se suspende nunca.")


@hoja
def defensor_54():
    pasos = fila(c(t("Comisión Mixta") + "<small>Congreso y Senado proponen candidato</small>", "", w=230), FH,
                 c(t("Congreso") + "<small>3/5</small>", "az", w=170), FH, c(t("Senado") + "<small>ratifica por 3/5 en 20 días</small>", "az", w=200), FH,
                 c(t("Elegido") + "<small>5 años</small>", "si", w=160))
    pasos2 = fila(c(t("Sin acuerdo") + "<small>nueva propuesta en un mes</small>", "no", w=230), FH,
                  c(t("Congreso") + "<small>3/5</small>", "az", w=170), FH, c(t("Senado") + "<small>basta mayoría absoluta</small>", "am", w=200), FH,
                  c(t("Elegido") + "<small>5 años</small>", "si", w=160))
    abajo = fila(c(t("Adjuntos") + "<small>Primero y Segundo: los nombra el Defensor con la conformidad de las Cámaras</small>", "gr", w="1"),
                 c(t("Requisitos") + "<small>español, mayor de edad, en pleno disfrute de sus derechos civiles y políticos</small>", "gr", w="1"),
                 c(t("Cese") + "<small>renuncia · fin del plazo · muerte o incapacidad · notoria negligencia · condena por delito doloso</small>", "gr", w="1.3"))
    pagina("defensor-54", "El Defensor del Pueblo", "Art. 54 CE y LO 3/1981: alto comisionado de las Cortes Generales",
           flujo('<div class="et az" style="align-self:flex-start">Primera ronda</div>', pasos, '<div style="height:14px"></div>',
                 '<div class="et no" style="align-self:flex-start">Segunda ronda</div>', pasos2, '<div style="height:26px"></div>', abajo),
           "En la segunda ronda se relaja <b>solo el Senado</b>. El Defensor no tiene título propio en la Constitución: está en el artículo 54.")


@hoja
def tc_159():
    arriba = c(t("Tribunal Constitucional") + "<small>12 magistrados nombrados por el Rey · 9 años · renovación por tercios cada 3</small>", "q", w=620)
    hijos = [c(t("4") + "<small>Congreso, por 3/5</small>", "az", w=200), c(t("4") + "<small>Senado, por 3/5</small>", "az", w=200),
             c(t("2") + "<small>Gobierno</small>", "", w=200), c(t("2") + "<small>CGPJ</small>", "", w=200)]
    abajo = fila(c(t("Quién puede serlo") + "<small>magistrados, fiscales, profesores de universidad, funcionarios y abogados, juristas de reconocida competencia con más de 15 años de ejercicio</small>", "gr", w="1.4"),
                 c(t("Presidente") + "<small>lo elige el Pleno entre sus miembros y lo nombra el Rey por 3 años</small>", "gr", w="1"),
                 extra="margin-top:30px")
    pagina("tc-159", "Composición del Tribunal Constitucional", "Arts. 159 y 160: doce magistrados, cuatro orígenes",
           flujo('<div style="display:flex;justify-content:center">%s</div>' % org(arriba, hijos), abajo),
           "El Senado elige a sus cuatro entre los candidatos que presentan las <b>Asambleas de las Comunidades Autónomas</b> (LOTC).")


@hoja
def tc_recursos():
    filas = [["Recurso de inconstitucionalidad<br><small>162.1.a</small>", "Leyes y normas con rango de ley", "Presidente del Gobierno · Defensor del Pueblo · 50 diputados · 50 senadores · órganos ejecutivos y Asambleas de las CCAA"],
             ["Cuestión de inconstitucionalidad<br><small>163</small>", "Una ley que el juez debe aplicar y que puede ser contraria a la CE", "El órgano judicial, de oficio o a instancia de parte"],
             ["Recurso de amparo<br><small>162.1.b</small>", "Violación del 14, la Sección 1.ª y el 30.2", "Toda persona natural o jurídica con interés legítimo · Defensor del Pueblo · Ministerio Fiscal"],
             ["Conflictos de competencia<br><small>161.1.c</small>", "Entre el Estado y las CCAA o de estas entre sí", "Gobierno y órganos de las CCAA"],
             ["Impugnación del 161.2", "Disposiciones y resoluciones de las CCAA", "El Gobierno: suspensión automática; el TC la ratifica o levanta en <b>5 meses</b>"]]
    pagina("tc-recursos", "Qué conoce el Tribunal Constitucional y quién recurre", "Arts. 161 a 163: los procesos y su legitimación",
           stage(tabla(["Proceso", "Qué se impugna", "Quién está legitimado"], filas, anchos=["250px", "270px", None])),
           "El <b>Defensor del Pueblo</b> está en los dos recursos: inconstitucionalidad y amparo. El Ministerio Fiscal, solo en amparo.")


@hoja
def reforma_167():
    izq = [c(t("Iniciativa") + "<small>Gobierno, Congreso, Senado y Asambleas de las CCAA (166). No hay iniciativa popular</small>", "gr", w=440), FV,
           c(t("3/5 de cada Cámara"), "az", w=440), FV,
           c("<b>Sin acuerdo:</b> comisión paritaria. Si no sale, <b>2/3 del Congreso</b> con mayoría absoluta del Senado", "bl", w=440), FV,
           c(t("Referéndum solo si lo pide 1/10") + "<small>de cualquiera de las Cámaras, en 15 días</small>", "si", w=440)]
    der = [c(t("Afecta a") + "<small>Título Preliminar · Sección 1.ª del Capítulo II del Título I · Título II, o revisión total</small>", "no", w=440), FV,
           c(t("2/3 de cada Cámara") + "<small>y disolución inmediata de las Cortes</small>", "az", w=440), FV,
           c("Las nuevas Cámaras ratifican y aprueban el texto por <b>2/3</b> en cada una", "bl", w=440), FV,
           c(t("Referéndum obligatorio"), "no", w=440)]
    col = lambda titulo, cls, xs: '<div style="display:flex;flex-direction:column;align-items:center"><div class="et %s">%s</div>%s</div>' % (cls, titulo, "".join(xs))
    pagina("reforma-167", "Reforma ordinaria y agravada", "Arts. 166 a 169: los dos caminos para reformar la Constitución",
           flujo(fila(col("Art. 167 · ordinaria", "az", izq), col("Art. 168 · agravada", "no", der), gap=60)),
           "No se puede iniciar una reforma en tiempo de guerra ni durante los estados del 116 (art. 169).")


# ====================== 02 · Tema 2 · Corona ======================
@hoja
def sucesion_57():
    pasos = [c(t("1 · Línea") + "<small>la anterior antes que las posteriores</small>", "az", w=210), FH,
             c(t("2 · Grado") + "<small>el más próximo antes que el más remoto</small>", "az", w=210), FH,
             c(t("3 · Sexo") + "<small>el varón antes que la mujer</small>", "az", w=210), FH,
             c(t("4 · Edad") + "<small>la persona de más edad antes que la de menos</small>", "az", w=210)]
    abajo = fila(c(t("57.2") + "<small>el heredero es Príncipe de Asturias desde su nacimiento</small>", "gr", w="1"),
                 c(t("57.3") + "<small>extinguidas todas las líneas, proveen las Cortes Generales</small>", "gr", w="1"),
                 c(t("57.4") + "<small>quien se case contra la prohibición del Rey y las Cortes queda excluido</small>", "gr", w="1"),
                 c(t("57.5") + "<small>abdicaciones, renuncias y dudas: por <b>ley orgánica</b></small>", "am", w="1"))
    pagina("sucesion-57", "Orden de sucesión a la Corona", "Art. 57.1: primogenitura y representación, en cadena",
           flujo(c("Corona hereditaria en los sucesores de <b>S. M. Don Juan Carlos I de Borbón</b>", "q", w=620, extra="align-self:center"), FV,
                 fila(*pasos, gap=6), '<div style="height:40px"></div>', abajo),
           "Se aplica en este orden y solo se pasa al siguiente criterio si hay empate en el anterior.")


@hoja
def regencia_59():
    p = flujo(
        c(t("¿Por qué no puede reinar el Rey?"), "q", w=480, extra="align-self:center"), FV,
        fila('<div style="display:flex;flex-direction:column;align-items:center;gap:0"><div class="et az">Es menor de edad · 59.1</div>%s</div>'
             % c("El <b>padre o la madre</b> del Rey; en su defecto, el pariente mayor de edad más próximo a suceder", "az", w=420),
             '<div style="display:flex;flex-direction:column;align-items:center;gap:0"><div class="et no">Está inhabilitado · 59.2</div>%s</div>'
             % c("El <b>Príncipe heredero</b> si es mayor de edad; si no, como en el 59.1. La inhabilitación la reconocen las Cortes", "no", w=420), gap=60),
        FV,
        c("<b>59.3</b> · Si no hay nadie: las <b>Cortes Generales</b> nombran una Regencia de <b>1, 3 o 5</b> personas", "bl", w=700, extra="align-self:center"),
        '<div style="height:22px"></div>',
        fila(c(t("Regente") + "<small>español y mayor de edad (59.4)</small>", "si", w=360),
             c(t("Tutor del Rey menor") + "<small>español <b>de nacimiento</b> y mayor de edad (60.1)</small>", "am", w=360)))
    pagina("regencia-59", "Regencia y tutela", "Arts. 59 y 60: quién ejerce la Corona cuando el Rey no puede", p,
           "Regente y tutor son incompatibles, salvo el padre, la madre o ascendientes directos del Rey (60.2).")


@hoja
def funciones_62():
    pagina("funciones-62", "Funciones del Rey", "Art. 62: diez letras, de la a) a la j)",
           mapa("<b>El Rey</b><small>Jefe del Estado, símbolo de su unidad y permanencia (56.1)</small>", [
               ("<b>a)</b> Sancionar y promulgar las leyes", "az"), ("<b>b)</b> Convocar y disolver las Cortes y convocar elecciones", ""),
               ("<b>c)</b> Convocar a referéndum", ""), ("<b>d)</b> Proponer, nombrar y cesar al Presidente del Gobierno", "az"),
               ("<b>e)</b> Nombrar y separar a los Ministros, a propuesta del Presidente", ""),
               ("<b>f)</b> Expedir decretos del Consejo de Ministros, conferir empleos y honores", ""),
               ("<b>g)</b> Ser informado y presidir el Consejo de Ministros si se lo pide el Presidente", "gr"),
               ("<b>h)</b> Mando supremo de las Fuerzas Armadas", "az"), ("<b>i)</b> Derecho de gracia; nunca indultos generales", "no"),
               ("<b>j)</b> Alto Patronazgo de las Reales Academias", "gr")], r=262, cw=200, alto=630, giro=math.pi / 10),
           None)


@hoja
def refrendo_64():
    p = flujo(
        c("<b>Los actos del Rey</b> serán siempre refrendados. Sin refrendo no son válidos (56.3)", "q", w=640, extra="align-self:center"), FV,
        fila(c(t("Regla general") + "<small>el <b>Presidente del Gobierno</b> y, en su caso, los Ministros competentes</small>", "az", w=440),
             c(t("Excepción") + "<small>el <b>Presidente del Congreso</b>: propuesta y nombramiento del Presidente del Gobierno y disolución del 99.5</small>", "am", w=440), gap=50),
        FV,
        c("De los actos del Rey son <b>responsables</b> las personas que los refrendan (64.2). La persona del Rey es inviolable", "si", w=640, extra="align-self:center"),
        '<div style="height:20px"></div>',
        c("<b>Sin refrendo</b>: la cantidad global de los Presupuestos para su Familia y Casa, que distribuye libremente, y nombrar y relevar a los miembros civiles y militares de su Casa (65)", "gr", w=900, extra="align-self:center"))
    pagina("refrendo-64", "El refrendo", "Art. 64: quién responde de los actos del Rey", p)


# ====================== 03 · Tema 3 · Cortes ======================
@hoja
def cortes_66():
    filas = [["Qué es", "Representa al pueblo español", "Cámara de representación territorial (69.1)"],
             ["Miembros", "De <b>300 a 400</b> diputados (hoy 350)", "4 por provincia + los insulares + 2 por Ceuta y 2 por Melilla + los autonómicos"],
             ["Circunscripción", "La provincia; Ceuta y Melilla, un diputado cada una", "La provincia; en las islas, cada isla o agrupación"],
             ["Sistema", "Sufragio universal, libre, igual, directo y secreto, con representación proporcional", "Sufragio universal, libre, igual, directo y secreto; los autonómicos los designa cada Comunidad"],
             ["Mandato", "4 años", "4 años"],
             ["Solo él", "Investidura, moción de censura, cuestión de confianza, convalidar decretos-leyes, autorizar la excepción y declarar el sitio", "Autorizar las medidas del 155 por mayoría absoluta"]]
    pagina("cortes-66", "Congreso y Senado", "Arts. 66 a 69: las dos Cámaras de las Cortes Generales, cara a cara",
           stage(tabla(["", "Congreso de los Diputados", "Senado"], filas, anchos=["170px", None, None])),
           "Las Cortes ejercen la potestad legislativa, aprueban los Presupuestos y controlan al Gobierno (66.2). Son inviolables (66.3).")


@hoja
def senado_69():
    b = [("Cada provincia", 4, ""), ("Gran Canaria, Mallorca, Tenerife", 3, ""), ("Las otras ocho islas", 1, "gr"),
         ("Ceuta y Melilla, cada una", 2, "v"), ("Cada Comunidad Autónoma", 1, "v"), ("+ por cada millón de habitantes", 1, "v")]
    h = '<div class="barras">'
    for txt, n, cls in b:
        h += '<div class="barra-f"><span>%s</span><i class="%s" style="width:%d%%">%d</i></div>' % (txt, cls, 18 * n + 6, n)
    h += "</div>"
    pagina("senado-69", "Cuántos senadores elige cada uno", "Art. 69: senadores por circunscripción",
           stage(h + '<p style="margin-top:22px;font-size:18px;color:var(--gris)">Las ocho islas menores: Ibiza, Formentera, Menorca, Fuerteventura, La Gomera, El Hierro, Lanzarote y La Palma. '
                 'Los senadores autonómicos (en verde) los designa la Asamblea legislativa de cada Comunidad.</p>'),
           "Ceuta y Melilla: <b>1 diputado</b> (68.2) pero <b>2 senadores</b> (69.4).")


@hoja
def fuentes_81():
    pir = ('<div class="pir">'
           + c(t("Ley orgánica") + "<small>art. 81 · derechos fundamentales, Estatutos, régimen electoral y las demás previstas · mayoría absoluta del Congreso en votación final</small>", "az", w=520)
           + c(t("Ley ordinaria") + "<small>mayoría simple · todo lo que no esté reservado a ley orgánica</small>", "", w=700)
           + fila(c(t("Decreto legislativo") + "<small>arts. 82 a 85 · el Gobierno, por delegación de las Cortes</small>", "si", w=440),
                  c(t("Decreto-ley") + "<small>art. 86 · el Gobierno, por extraordinaria y urgente necesidad</small>", "am", w=440), gap=20)
           + c(t("Reglamento") + "<small>potestad reglamentaria del Gobierno (97), siempre por debajo de la ley</small>", "gr", w=920) + "</div>")
    pagina("fuentes-81", "Las normas con rango de ley", "Arts. 81 a 86: quién hace cada norma y con qué mayoría", stage(pir),
           "La delegación del 82 es en forma expresa, para materia concreta y con plazo. No cabe para leyes orgánicas ni puede subdelegarse.")


@hoja
def delegacion_82():
    p = flujo(
        c(t("Delegación legislativa") + "<small>las Cortes delegan en el Gobierno dictar normas con rango de ley (82.1)</small>", "q", w=620, extra="align-self:center"), FV,
        fila(c(t("Ley de bases") + "<small>para formar <b>textos articulados</b></small>", "az", w=400),
             c(t("Ley ordinaria") + "<small>para <b>refundir</b> varios textos legales en uno</small>", "az", w=400), gap=60), FV,
        fila(c("<b>Expresa</b>", "si", w=180), c("<b>Materia concreta</b>", "si", w=190), c("<b>Plazo fijado</b>", "si", w=180),
             c("<b>Se agota</b> al publicarse la norma", "si", w=220), gap=14),
        '<div style="height:22px"></div>',
        fila(c("<b>No</b> por tiempo indeterminado", "no", w=260), c("<b>No</b> a favor de otras autoridades", "no", w=280), c("<b>No</b> en materias de ley orgánica", "no", w=280), gap=14))
    pagina("delegacion-82", "Legislación delegada", "Arts. 82 a 85: el resultado se llama <b>decreto legislativo</b>", p,
           "Las leyes de bases no pueden autorizar a modificar la propia ley de bases ni dictar normas con carácter retroactivo (83).")


@hoja
def decreto_ley_86():
    h = eje([(0.1, "Día 0", "El Gobierno aprueba el <b>decreto-ley</b>: extraordinaria y urgente necesidad", True, "az"),
             (0.33, "Promulgación", "Entra en vigor como disposición <b>provisional</b>", False, ""),
             (0.66, "Hasta 30 días", "El <b>Congreso</b> debate y vota: <b>convalida o deroga</b>", True, "am"),
             (0.88, "Después", "Puede tramitarse como <b>proyecto de ley</b> por urgencia", False, "si")], alto=430)
    no = fila(c("<b>No puede afectar a:</b> instituciones básicas del Estado · derechos, deberes y libertades del Título I · régimen de las CCAA · Derecho electoral general", "no", w=930))
    pagina("decreto-ley-86", "El decreto-ley", "Art. 86: plazos y límites", stage(h + no),
           "Lo vota <b>solo el Congreso</b>, en votación de totalidad. Si no está reunido, se le convoca para ello.")


@hoja
def legislativo_90():
    a = fila(c(t("Iniciativa") + "<small>Gobierno (proyecto) · Congreso, Senado, Asambleas de las CCAA o 500.000 firmas (proposición)</small>", "gr", w=300), FH,
             c(t("Congreso") + "<small>aprueba el texto</small>", "az", w=180), FH,
             c(t("Senado") + "<small><b>2 meses</b>; <b>20 días naturales</b> si es urgente</small>", "az", w=240), FH,
             c(t("Rey") + "<small>sanciona en <b>15 días</b>, promulga y ordena publicar</small>", "si", w=200))
    b = fila(c(t("Veto") + "<small>mayoría absoluta del Senado</small>", "no", w=300), FH,
             c("El Congreso lo levanta por <b>mayoría absoluta</b> en el acto o por <b>mayoría simple</b> pasados 2 meses", "bl", w=420), gap=10)
    e = fila(c(t("Enmiendas") + "<small>mayoría simple del Senado</small>", "am", w=300), FH,
             c("El Congreso las acepta o rechaza por <b>mayoría simple</b>", "bl", w=420), gap=10)
    pagina("legislativo-90", "Cómo se hace una ley", "Arts. 87 a 91: de la iniciativa a la publicación",
           flujo(a, '<div style="height:40px"></div>', '<div class="et no" style="align-self:center">Si el Senado se opone</div>', b, '<div style="height:14px"></div>', e))


@hoja
def iniciativa_87():
    pagina("iniciativa-87", "Iniciativa legislativa", "Art. 87: quién puede poner en marcha una ley",
           mapa("<b>Iniciativa legislativa</b><small>art. 87</small>", [
               ("<b>Gobierno</b><small>proyectos de ley (88), aprobados en Consejo de Ministros</small>", "az"),
               ("<b>Congreso</b><small>proposiciones de ley, según su Reglamento</small>", ""),
               ("<b>Senado</b><small>proposiciones de ley, que pasan al Congreso</small>", ""),
               ("<b>Asambleas de las CCAA</b><small>piden un proyecto al Gobierno o remiten una proposición al Congreso, con hasta 3 miembros</small>", "gr"),
               ("<b>Iniciativa popular</b><small>500.000 firmas · no en leyes orgánicas, tributarias, internacionales ni de gracia</small>", "si")], r=230, cw=290, alto=600),
           "En la <b>reforma constitucional</b> no hay iniciativa popular (166 remite solo a los apartados 1 y 2 del 87).")


@hoja
def tratados_93():
    p = flujo(
        c(t("¿Qué tratado es?"), "q", w=420, extra="align-self:center"), FV,
        fila(c(t("Art. 93") + "<small>atribuye a una organización internacional competencias derivadas de la Constitución</small><div style='margin-top:8px'><b>Ley orgánica</b></div>", "az", w=290),
             c(t("Art. 94.1") + "<small>políticos o militares · integridad territorial · derechos del Título I · obligaciones financieras · modifican o exigen leyes</small><div style='margin-top:8px'><b>Autorización previa de las Cortes</b></div>", "", w=330),
             c(t("Art. 94.2") + "<small>todos los demás</small><div style='margin-top:8px'><b>Se informa a las Cámaras</b> de inmediato</div>", "gr", w=290), gap=24),
        '<div style="height:26px"></div>',
        c("<b>Art. 95</b> · Si contiene estipulaciones contrarias a la Constitución, hace falta <b>reformarla antes</b>. El Gobierno o cualquiera de las Cámaras pueden pedir al TC que lo declare", "am", w=900, extra="align-self:center"))
    pagina("tratados-93", "Tratados internacionales", "Arts. 93 a 96: qué autorización necesita cada uno", p,
           "Los tratados válidamente celebrados forman parte del ordenamiento interno una vez publicados en España (96.1).")


# ====================== 04 · Tema 4 · Poder Judicial ======================
@hoja
def judicial_117():
    pagina("judicial-117", "Principios del Poder Judicial", "Arts. 117 a 121: cómo se administra la justicia",
           mapa("<b>La justicia</b><small>emana del pueblo y se administra en nombre del Rey (117.1)</small>", [
               ("<b>Jueces y Magistrados</b><small>independientes, inamovibles, responsables y sometidos solo al imperio de la ley</small>", "az"),
               ("<b>Unidad jurisdiccional</b><small>base de la organización de los Tribunales (117.5)</small>", ""),
               ("<b>Exclusividad</b><small>juzgar y hacer ejecutar lo juzgado (117.3)</small>", ""),
               ("<b>Participación</b><small>acción popular y jurado (125)</small>", "gr"),
               ("<b>Gratuidad</b><small>cuando la ley lo disponga y para quien no tenga recursos (119)</small>", "gr"),
               ("<b>Publicidad y oralidad</b><small>actuaciones públicas; procedimiento sobre todo oral (120)</small>", "si"),
               ("<b>Responsabilidad del Estado</b><small>por error judicial o mal funcionamiento (121)</small>", "si")], r=235, cw=270, alto=600),
           "Jueces y Magistrados en activo <b>no pueden pertenecer</b> a partidos ni sindicatos (127.1).")


@hoja
def cgpj_122():
    arriba = c(t("Consejo General del Poder Judicial") + "<small>lo preside el Presidente del Tribunal Supremo · 20 vocales nombrados por el Rey por 5 años</small>", "q", w=680)
    hijos = [c(t("12") + "<small>entre Jueces y Magistrados de todas las categorías</small>", "az", w=260),
             c(t("4") + "<small>propuestos por el Congreso por 3/5</small>", "", w=230),
             c(t("4") + "<small>propuestos por el Senado por 3/5</small>", "", w=230)]
    abajo = fila(c("Los 8 de las Cámaras: <b>abogados y otros juristas</b> de reconocida competencia con más de <b>15 años</b> de ejercicio", "gr", w=520),
                 c(t("Funciones") + "<small>nombramientos, ascensos, inspección y régimen disciplinario de jueces</small>", "gr", w=380), extra="margin-top:34px")
    pagina("cgpj-122", "El Consejo General del Poder Judicial", "Art. 122: el órgano de gobierno de los jueces",
           flujo('<div style="display:flex;justify-content:center">%s</div>' % org(arriba, hijos), abajo),
           "El Presidente del Tribunal Supremo lo nombra el Rey <b>a propuesta del CGPJ</b> (123.2). El Fiscal General, a propuesta del <b>Gobierno</b>, oído el CGPJ (124.4).")


@hoja
def tribunales():
    raiz = c(t("Tribunal Supremo") + "<small>Madrid · órgano superior en todos los órdenes, salvo garantías constitucionales (123)</small>", "q", w=520)
    nivel2 = [c(t("Audiencia Nacional") + "<small>Madrid · toda España</small>", "az", w=220),
              c(t("Tribunales Superiores de Justicia") + "<small>una Comunidad Autónoma</small>", "az", w=250),
              c(t("Audiencias Provinciales") + "<small>una provincia</small>", "", w=220),
              c(t("Juzgados") + "<small>partido judicial, provincia o toda España</small>", "", w=220)]
    pagina("tribunales", "Juzgados y tribunales", "LOPJ: cómo se organiza territorialmente la justicia",
           flujo('<div style="display:flex;justify-content:center">%s</div>' % org(raiz, nivel2),
                 fila(c("<b>Planta territorial</b> (art. 30 LOPJ): municipios, partidos judiciales, provincias y Comunidades Autónomas", "gr", w=930), extra="margin-top:40px")),
           "El Tribunal Supremo tiene cinco Salas: Civil, Penal, Contencioso-administrativo, Social y <b>Militar</b>. La Audiencia Nacional no juzga ni lo civil ni lo militar.")


# ====================== 05 · Tema 5 · Gobierno ======================
@hoja
def gobierno_98():
    raiz = c(t("Gobierno") + "<small>art. 98 CE · art. 1 Ley 50/1997</small>", "q", w=420)
    hijos = [c(t("Presidente") + "<small>dirige la acción del Gobierno y coordina a sus miembros</small>", "az", w=250),
             c(t("Vicepresidentes") + "<small>en su caso; uno o varios</small>", "", w=230),
             c(t("Ministros") + "<small>al frente de un departamento; puede haber sin cartera</small>", "", w=250)]
    col = fila(c(t("Consejo de Ministros") + "<small>órgano colegiado</small>", "si", w="1"), c(t("Comisiones Delegadas") + "<small>órganos colegiados</small>", "si", w="1"),
               extra="margin-top:30px")
    apoyo = fila(c("<b>Órganos de colaboración y apoyo</b> (Ley 50/1997): Secretarios de Estado · Comisión General de Secretarios de Estado y Subsecretarios · Secretariado del Gobierno · Gabinetes", "gr", w=930),
                 extra="margin-top:14px")
    pagina("gobierno-98", "Composición del Gobierno", "Art. 98 CE y Ley 50/1997, del Gobierno",
           flujo('<div style="display:flex;justify-content:center">%s</div>' % org(raiz, hijos), col, apoyo),
           "Los <b>Secretarios de Estado</b> no son miembros del Gobierno. Las deliberaciones del Consejo de Ministros son secretas.")


@hoja
def investidura_99():
    p = flujo(
        fila(c(t("Consultas") + "<small>el Rey, con los representantes de los grupos políticos</small>", "gr", w=250), FH,
             c(t("Propuesta") + "<small>el Rey propone candidato a través del Presidente del Congreso</small>", "", w=280), FH,
             c(t("1.ª votación") + "<small>mayoría <b>absoluta</b></small>", "az", w=200), FH,
             c(t("Investido") + "<small>el Rey lo nombra</small>", "si", w=160)),
        '<div style="height:16px"></div>',
        '<div class="et no" style="align-self:center">Si no la obtiene</div>',
        fila(c(t("2.ª votación") + "<small><b>48 horas</b> después, mayoría <b>simple</b></small>", "az", w=280), FH,
             c(t("Nuevas propuestas") + "<small>si tampoco la obtiene</small>", "", w=250), FH,
             c(t("2 meses") + "<small>desde la primera votación sin investidura</small>", "am", w=230), FH,
             c(t("Disolución") + "<small>el Rey disuelve las dos Cámaras y convoca elecciones</small>", "no", w=230)))
    pagina("investidura-99", "La investidura", "Art. 99: cómo se elige al Presidente del Gobierno", p,
           "La disolución del 99.5 la refrenda el <b>Presidente del Congreso</b>, no el del Gobierno.")


@hoja
def confianza_112():
    filas = [["Quién la plantea", "El Presidente, previa deliberación del Consejo de Ministros", "Al menos <b>1/10</b> de los diputados, con candidato"],
             ["Sobre qué", "Su programa o una declaración de política general", "Exigir la responsabilidad política del Gobierno"],
             ["Mayoría", "<b>Simple</b> para otorgarla", "<b>Absoluta</b> para aprobarla"],
             ["Plazos", "No hay espera para votar", "No se vota antes de <b>5 días</b>; en los 2 primeros, mociones alternativas"],
             ["Si sale mal", "Si se niega, el Gobierno dimite y se va al 99", "Si no prospera, sus firmantes no repiten en ese periodo de sesiones"],
             ["Si sale bien", "El Gobierno sigue", "El Gobierno dimite y el <b>candidato queda investido</b>"]]
    pagina("confianza-112", "Cuestión de confianza y moción de censura", "Arts. 112 a 114: la responsabilidad política del Gobierno ante el Congreso",
           stage(tabla(["", "Cuestión de confianza (112)", "Moción de censura (113)"], filas, anchos=["170px", None, None])),
           "Las dos son <b>solo ante el Congreso</b>. El Presidente no puede proponer la disolución mientras se tramita una moción de censura (115.2).")


@hoja
def cese_101():
    causas = [c(t("Elecciones") + "<small>tras celebrarse las generales</small>", "az", w="1"), c(t("Confianza perdida") + "<small>cuestión o moción (112 y 113)</small>", "az", w="1"),
              c(t("Dimisión") + "<small>del Presidente</small>", "az", w="1"), c(t("Fallecimiento") + "<small>del Presidente</small>", "az", w="1")]
    no = c("<b>El Gobierno en funciones no puede</b> (art. 21 Ley 50/1997): aprobar el proyecto de Presupuestos · presentar proyectos de ley a las Cortes<br>"
           "<b>Su Presidente no puede</b>: proponer la disolución de las Cámaras · plantear la cuestión de confianza · proponer un referéndum consultivo", "no izq", w=930)
    pagina("cese-101", "Cese y Gobierno en funciones", "Art. 101 CE y art. 21 de la Ley 50/1997",
           flujo(fila(*causas), FV, c("Sigue <b>en funciones</b> hasta que toma posesión el nuevo Gobierno (101.2)", "q", w=700, extra="align-self:center"), FV, no),
           "El Gobierno en funciones se limita al <b>despacho ordinario</b> de los asuntos públicos, salvo urgencia o interés general.")


@hoja
def normas_gobierno():
    pir = ('<div class="pir">'
           + c(t("Real Decreto del Presidente del Gobierno") + "<small>y Real Decreto acordado en Consejo de Ministros</small>", "az", w=560)
           + c(t("Orden Ministerial") + "<small>disposiciones de los Ministros; también las de las Comisiones Delegadas, por orden del Ministro competente o del de la Presidencia</small>", "", w=780)
           + "</div>")
    lado = fila(c("<b>Forma de los actos</b> (art. 24.1): Reales Decretos Legislativos y Reales Decretos-leyes · Reales Decretos del Presidente · Reales Decretos del Consejo de Ministros · Acuerdos del Consejo de Ministros · Acuerdos de Comisiones Delegadas · Órdenes Ministeriales", "gr", w=930),
                extra="margin-top:30px")
    pagina("normas-gobierno", "Jerarquía de las normas del Gobierno", "Art. 24 de la Ley 50/1997: quién dicta qué y en qué orden", stage(pir + lado),
           "Un reglamento no puede vulnerar lo que dispone otro de rango superior (art. 24.2).")


@hoja
def administracion_103():
    p = flujo(
        c("<b>Art. 103.1</b> · La Administración sirve con objetividad los intereses generales", "q", w=700, extra="align-self:center"), FV,
        fila(c("<b>Eficacia</b>", "az", w=170), c("<b>Jerarquía</b>", "az", w=170), c("<b>Descentralización</b>", "az", w=200),
             c("<b>Desconcentración</b>", "az", w=200), c("<b>Coordinación</b>", "az", w=180), gap=12),
        '<div style="height:10px"></div>',
        c("con <b>sometimiento pleno a la ley y al Derecho</b>", "si", w=520, extra="align-self:center"),
        '<div style="height:28px"></div>',
        fila(c(t("103.3") + "<small>acceso a la función pública según mérito y capacidad</small>", "gr", w="1"),
             c(t("104") + "<small>Fuerzas y Cuerpos de Seguridad, bajo el Gobierno</small>", "gr", w="1"),
             c(t("105") + "<small>audiencia, acceso a archivos y procedimiento</small>", "gr", w="1"),
             c(t("106") + "<small>los Tribunales controlan la potestad reglamentaria</small>", "gr", w="1"),
             c(t("107") + "<small>Consejo de Estado, supremo órgano consultivo</small>", "gr", w="1")))
    pagina("administracion-103", "La Administración Pública", "Arts. 103 a 107: los cinco principios del 103.1", p)


# ====================== 06 · Economía y territorio ======================
@hoja
def territorial_137():
    raiz = c(t("El Estado se organiza en") + "<small>art. 137 · todas gozan de autonomía para gestionar sus intereses</small>", "q", w=560)
    hijos = [c(t("Municipios") + "<small>art. 140 · autonomía y personalidad jurídica plena; alcaldes y concejales</small>", "az", w=290),
             c(t("Provincias") + "<small>art. 141 · agrupación de municipios; gobierno de Diputaciones</small>", "az", w=290),
             c(t("Comunidades Autónomas") + "<small>arts. 143 y ss. · Estatuto como norma institucional básica</small>", "az", w=290)]
    abajo = fila(c(t("Art. 138") + "<small>el Estado garantiza la solidaridad y un equilibrio económico adecuado y justo, atendiendo al hecho insular</small>", "gr", w="1"),
                 c(t("Art. 139") + "<small>todos los españoles tienen los mismos derechos y obligaciones en cualquier parte del territorio</small>", "gr", w="1"), extra="margin-top:34px")
    pagina("territorial-137", "Organización territorial del Estado", "Título VIII: municipios, provincias y Comunidades Autónomas",
           flujo('<div style="display:flex;justify-content:center">%s</div>' % org(raiz, hijos), abajo),
           "En las islas, los <b>Cabildos o Consejos</b> también tienen su administración propia (141.4).")


@hoja
def acceso_143():
    filas = [["Iniciativa", "Diputaciones interesadas y <b>2/3 de los municipios</b> que sean mayoría del censo de cada provincia o isla", "Además, <b>3/4 de los municipios</b> de cada provincia que sean mayoría del censo"],
             ["Plazo", "6 meses desde el primer acuerdo; si no prospera, se reintenta pasados 5 años (143.3)", "6 meses"],
             ["Ratificación", "No necesita referéndum", "<b>Referéndum</b>: mayoría absoluta de los electores de cada provincia"],
             ["Competencias", "Las del 148; ampliables pasados <b>5 años</b> (148.2)", "Más competencias desde el principio, dentro de los límites del 149"]]
    pagina("acceso-143", "Las dos vías hacia la autonomía", "Arts. 143 y 151: vía ordinaria y vía rápida",
           stage(tabla(["", "Vía del 143 (ordinaria)", "Vía del 151 (rápida)"], filas, anchos=["170px", None, None])),
           "Las Cortes pueden, por razones de interés nacional y mediante <b>ley orgánica</b>, autorizar o acordar una autonomía fuera de estas reglas (144).")


@hoja
def competencias_148():
    venn = ('<svg viewBox="0 0 1027 590" style="width:100%;height:100%"><g transform="translate(0,40)">'
            '<circle cx="380" cy="290" r="255" fill="#e3edfa" stroke="#1466d9" stroke-width="3" fill-opacity=".85"/>'
            '<circle cx="650" cy="290" r="255" fill="#e0f3ea" stroke="#168a5b" stroke-width="3" fill-opacity=".75"/>'
            '<text x="270" y="-14" font-size="24" font-weight="700" fill="#1466d9" text-anchor="middle">Art. 149 · Estado</text>'
            '<text x="760" y="-14" font-size="24" font-weight="700" fill="#168a5b" text-anchor="middle">Art. 148 · CCAA</text>'
            '<g font-size="16" fill="#1f2937" text-anchor="middle">'
            '<text x="272" y="190">Nacionalidad, extranjería</text><text x="272" y="216">y asilo · relaciones</text><text x="272" y="242">internacionales · defensa</text>'
            '<text x="272" y="282">Administración de Justicia</text><text x="272" y="308">legislación mercantil, penal</text><text x="272" y="334">y laboral · Hacienda general</text>'
            '<text x="272" y="374">bases y coordinación</text><text x="272" y="400">de la sanidad · 32 materias</text>'
            '<text x="758" y="190">Organización de sus</text><text x="758" y="216">instituciones · urbanismo</text><text x="758" y="242">y vivienda · obras públicas</text>'
            '<text x="758" y="282">de su interés · agricultura</text><text x="758" y="308">montes · turismo · deporte</text><text x="758" y="334">asistencia social · 22 materias</text></g>'
            '<g font-size="18" text-anchor="middle" fill="#1f2d44"><text x="515" y="250" font-weight="700">Compartidas</text>'
            '<text x="515" y="278">el Estado fija</text><text x="515" y="302">las bases y la CA</text><text x="515" y="326">las desarrolla</text></g></g></svg>')
    pagina("competencias-148", "Competencias del Estado y de las Comunidades", "Arts. 148 a 150: quién hace qué",
           stage(venn), "<b>Cláusula residual</b> (149.3): lo que no asuman los Estatutos es del Estado, y su Derecho es <b>supletorio</b> del autonómico.")


@hoja
def hacienda_134():
    p = flujo(
        fila(c(t("Gobierno") + "<small>elabora los Presupuestos Generales</small>", "az", w=260), FH,
             c(t("Congreso") + "<small>los recibe al menos <b>3 meses</b> antes de que expiren los del año anterior</small>", "", w=300), FH,
             c(t("Cortes") + "<small>examinan, enmiendan y aprueban</small>", "si", w=260)),
        '<div style="height:16px"></div>',
        c("Si no se aprueban antes del primer día del ejercicio, se <b>prorrogan automáticamente</b> los anteriores (134.4)", "am", w=760, extra="align-self:center"),
        '<div style="height:28px"></div>',
        fila(c(t("Anuales") + "<small>e incluyen todos los gastos e ingresos del sector público estatal</small>", "gr", w="1"),
             c(t("No crean tributos") + "<small>solo pueden modificarlos si una ley tributaria lo prevé (134.7)</small>", "no", w="1"),
             c(t("Art. 135") + "<small>estabilidad presupuestaria; pagar la deuda pública tiene prioridad absoluta</small>", "gr", w="1"),
             c(t("Art. 136") + "<small>Tribunal de Cuentas, supremo órgano fiscalizador; depende de las Cortes</small>", "gr", w="1")))
    pagina("hacienda-134", "Los Presupuestos Generales del Estado", "Título VII · Economía y Hacienda (arts. 128 a 136)", p,
           "Toda proposición o enmienda que aumente el gasto o reduzca los ingresos necesita la <b>conformidad del Gobierno</b> (134.6).")


def pintar(nombre):
    png = os.path.join(AQUI, nombre + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2.14",
                    "--window-size=1123,794", "--screenshot=" + png, "file://" + os.path.join(AQUI, nombre + ".html")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


if __name__ == "__main__":
    ids = sys.argv[1:] or list(HOJAS)
    for n in ids:
        HOJAS[n]()
        pintar(n)
    print(len(ids), "hojas")
