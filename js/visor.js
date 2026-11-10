/* Visor de apuntes: abre los esquemas de una pregunta en una ventana con zoom y arrastre.
   Escritorio: rueda para acercar, arrastrar con el ratón. Móvil: pellizco y arrastre con un dedo.
   En móvil vertical, la ventana se gira un cuarto de vuelta para que el esquema apaisado se vea grande. */
(function () {
  "use strict";
  var ZOOM_MAX = 6, PASO = 1.35;
  var visor, escenario, lienzo, imagen, titulo, cuenta, bAnt, bSig;
  var lista = [], pos = 0, opener = null;
  var z = 1, tx = 0, ty = 0, ajuste = 1;          // zoom relativo al ajuste, desplazamiento
  var punteros = {}, gesto = null, giro = false;
  var suave = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  var CERRAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var MAS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
  var MENOS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14"/></svg>';
  var ANT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>';
  var SIG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>';

  function crear() {
    visor = document.createElement("dialog");
    visor.className = "visor";
    visor.setAttribute("aria-label", "Apuntes");
    visor.innerHTML =
      '<div class="visor-cab">' +
        '<div class="visor-tit"><h2 id="visor-titulo"></h2><p id="visor-cuenta"></p></div>' +
        '<div class="visor-herr">' +
          '<button type="button" class="visor-b" data-v="ant" aria-label="Página o apunte anterior">' + ANT + '</button>' +
          '<button type="button" class="visor-b" data-v="sig" aria-label="Página o apunte siguiente">' + SIG + '</button>' +
          '<button type="button" class="visor-b visor-zoom" data-v="menos" aria-label="Alejar">' + MENOS + '</button>' +
          '<button type="button" class="visor-b visor-zoom" data-v="mas" aria-label="Acercar">' + MAS + '</button>' +
        '</div>' +
        '<button type="button" class="visor-x" data-v="cerrar" aria-label="Cerrar apuntes">' + CERRAR + '</button>' +
      '</div>' +
      '<div class="visor-esc" tabindex="0" role="img" aria-label="Esquema. Con el teclado, flechas para mover, más y menos para el zoom."><div class="visor-lienzo"><img class="visor-img" alt="" draggable="false"></div></div>';
    document.body.appendChild(visor);
    escenario = visor.querySelector(".visor-esc");
    lienzo = visor.querySelector(".visor-lienzo");
    imagen = visor.querySelector(".visor-img");
    titulo = visor.querySelector("#visor-titulo");
    cuenta = visor.querySelector("#visor-cuenta");
    bAnt = visor.querySelector('[data-v="ant"]');
    bSig = visor.querySelector('[data-v="sig"]');

    visor.addEventListener("click", function (e) {
      var b = e.target.closest("[data-v]");
      if (b) {
        var a = b.getAttribute("data-v");
        if (a === "cerrar") cerrar();
        else if (a === "ant") ir(pos - 1);
        else if (a === "sig") ir(pos + 1);
        else if (a === "mas") zoomCentro(PASO);
        else if (a === "menos") zoomCentro(1 / PASO);
        return;
      }
      if (e.target === visor) cerrar();   // clic en la zona oscura de fuera
    });
    visor.addEventListener("close", function () { imagen.removeAttribute("src"); if (opener && opener.focus) opener.focus(); });
    escenario.addEventListener("wheel", rueda, { passive: false });
    escenario.addEventListener("pointerdown", abajo);
    escenario.addEventListener("pointermove", mueve);
    escenario.addEventListener("pointerup", arriba);
    escenario.addEventListener("pointercancel", arriba);
    escenario.addEventListener("dblclick", function (e) { var p = local(e); if (z > 1.05) ajustar(); else zoomEn(3, p.x, p.y); });
    escenario.addEventListener("keydown", tecla);
    // Si la ventana cambia de tamaño o se gira el móvil, el esquema se vuelve a ajustar.
    if (window.ResizeObserver) new ResizeObserver(function () { if (visor.open && lista.length) { medir(); ajustar(true); } }).observe(escenario);
    imagen.addEventListener("load", function () { medir(); ajustar(true); });
  }

  /* El giro solo ocurre en móvil vertical; el CSS lo decide y aquí se lee el resultado. */
  function medir() {
    giro = getComputedStyle(visor).getPropertyValue("--giro").trim() === "1";
  }
  /* Coordenadas del puntero dentro del escenario, ya con el giro deshecho. */
  function local(e) {
    var r = escenario.getBoundingClientRect(), x, y;
    if (giro) { x = e.clientY - r.top; y = r.right - e.clientX; }   // 90° en sentido horario
    else { x = e.clientX - r.left; y = e.clientY - r.top; }
    return { x: x, y: y };
  }
  /* offsetWidth y offsetHeight no cambian con el giro: ya son el ancho y el alto del escenario girado. */
  function tam() { return { w: escenario.offsetWidth, h: escenario.offsetHeight }; }

  function aplicar() {
    var it = lista[pos], s = ajuste * z;
    var t = tam(), w = it.w * s, h = it.h * s;
    // El esquema no se puede soltar fuera: si cabe, va centrado; si no, se queda pegado a los bordes.
    tx = w <= t.w ? (t.w - w) / 2 : Math.min(0, Math.max(t.w - w, tx));
    ty = h <= t.h ? (t.h - h) / 2 : Math.min(0, Math.max(t.h - h, ty));
    lienzo.style.width = it.w + "px"; lienzo.style.height = it.h + "px";
    lienzo.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")";
    escenario.classList.toggle("ampliado", z > 1.02);
  }
  function ajustar(sinAviso) {
    var it = lista[pos], t = tam();
    var margen = 16;
    ajuste = Math.min((t.w - margen) / it.w, (t.h - margen) / it.h);
    z = 1; tx = 0; ty = 0;
    aplicar();
  }
  function zoomEn(nuevo, x, y) {
    nuevo = Math.min(ZOOM_MAX, Math.max(1, nuevo));
    var antes = ajuste * z, despues = ajuste * nuevo;
    // El punto bajo el cursor se queda quieto mientras cambia el tamaño.
    tx = x - (x - tx) * despues / antes;
    ty = y - (y - ty) * despues / antes;
    z = nuevo; aplicar();
  }
  function zoomCentro(factor) { var t = tam(); zoomEn(z * factor, t.w / 2, t.h / 2); }

  function rueda(e) {
    e.preventDefault();
    var p = local(e), d = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
    zoomEn(z * Math.exp(-d * 0.0015), p.x, p.y);
  }
  function abajo(e) {
    escenario.setPointerCapture(e.pointerId);
    punteros[e.pointerId] = local(e);
    reiniciarGesto();
    escenario.classList.add("agarrado");
  }
  function reiniciarGesto() {
    var ids = Object.keys(punteros);
    if (ids.length === 1) gesto = { tipo: "mover", p: punteros[ids[0]], tx: tx, ty: ty };
    else if (ids.length >= 2) {
      var a = punteros[ids[0]], b = punteros[ids[1]];
      gesto = { tipo: "pellizco", d: Math.hypot(a.x - b.x, a.y - b.y) || 1, z: z, c: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }, tx: tx, ty: ty };
    } else gesto = null;
  }
  function mueve(e) {
    if (!punteros[e.pointerId]) return;
    punteros[e.pointerId] = local(e);
    if (!gesto) return;
    var ids = Object.keys(punteros);
    if (gesto.tipo === "mover" && ids.length === 1) {
      var p = punteros[ids[0]];
      tx = gesto.tx + (p.x - gesto.p.x); ty = gesto.ty + (p.y - gesto.p.y);
      aplicar();
    } else if (gesto.tipo === "pellizco" && ids.length >= 2) {
      var a = punteros[ids[0]], b = punteros[ids[1]];
      var d = Math.hypot(a.x - b.x, a.y - b.y) || 1, c = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      var nuevo = Math.min(ZOOM_MAX, Math.max(1, gesto.z * d / gesto.d));
      var antes = ajuste * gesto.z, despues = ajuste * nuevo;
      tx = c.x - (gesto.c.x - gesto.tx) * despues / antes;
      ty = c.y - (gesto.c.y - gesto.ty) * despues / antes;
      z = nuevo; aplicar();
    }
  }
  function arriba(e) {
    delete punteros[e.pointerId];
    reiniciarGesto();
    if (!Object.keys(punteros).length) escenario.classList.remove("agarrado");
  }
  function tecla(e) {
    var t = tam(), paso = 80;
    if (e.key === "+" || e.key === "=") { e.preventDefault(); zoomCentro(PASO); }
    else if (e.key === "-" || e.key === "_") { e.preventDefault(); zoomCentro(1 / PASO); }
    else if (e.key === "0") { e.preventDefault(); ajustar(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); if (z > 1.02) { tx += paso; aplicar(); } else ir(pos - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); if (z > 1.02) { tx -= paso; aplicar(); } else ir(pos + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); ty += paso; aplicar(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); ty -= paso; aplicar(); }
  }

  function ir(n) {
    if (n < 0 || n >= lista.length) return;
    pos = n; pintar();
  }
  function pintar() {
    var it = lista[pos];
    titulo.textContent = it.titulo;
    var partes = [];
    if (it.total > 1) partes.push("Página " + it.n + " de " + it.total);
    var distintos = [];
    lista.forEach(function (x) { if (distintos.indexOf(x.id) < 0) distintos.push(x.id); });
    if (distintos.length > 1) partes.push("Apunte " + (distintos.indexOf(it.id) + 1) + " de " + distintos.length);
    cuenta.textContent = partes.join(" · ");
    bAnt.hidden = bSig.hidden = lista.length < 2;
    bAnt.disabled = pos === 0; bSig.disabled = pos === lista.length - 1;
    imagen.alt = it.titulo;
    escenario.setAttribute("aria-label", "Esquema: " + it.titulo + ". Con el teclado, flechas para mover, más y menos para el zoom, cero para ajustar.");
    if (imagen.getAttribute("src") === it.src && imagen.complete) { medir(); ajustar(true); }
    else imagen.src = it.src;
  }

  function cerrar() {
    var cierra = function () { if (visor.close) visor.close(); else visor.removeAttribute("open"); };
    if (window.Mov) window.Mov.dialogoSale(visor, false, cierra); else cierra();
  }

  /* ids: lista de esquemas del catálogo (window.ESQUEMAS). Cada página es una vista distinta. */
  window.abrirVisor = function (ids, quien, inicio) {
    if (!visor) crear();
    lista = [];
    ids.forEach(function (id) {
      var e = window.ESQUEMAS && window.ESQUEMAS[id]; if (!e) return;
      e.paginas.forEach(function (pg, i) {
        lista.push({ id: id, titulo: e.titulo, src: pg.src, w: pg.w, h: pg.h, n: i + 1, total: e.paginas.length });
      });
    });
    if (!lista.length) return;
    opener = quien || null; pos = 0;
    for (var k = 0; k < lista.length; k++) if (lista[k].id === inicio) { pos = k; break; }
    if (!visor.open) { if (visor.showModal) visor.showModal(); else visor.setAttribute("open", ""); }
    if (window.Mov) window.Mov.dialogoEntra(visor, false);
    medir(); pintar();
    escenario.focus({ preventScroll: true });
  };
})();
