/* Movimiento de la app con GSAP: entradas de pantalla, cambio de pregunta, respuestas, acordeones, diálogos y resultados.
   Reglas: duraciones cortas (de 0,12 a 0,6 s), nunca se bloquea la respuesta más de lo que dura la salida (0,12 s),
   y con "reducir movimiento" activado no se anima nada. Si GSAP no carga, la app funciona igual, sin movimiento. */
(function () {
  "use strict";
  var g = window.gsap, F = window.Flip;
  if (g && F) g.registerPlugin(F);
  var reducido = window.matchMedia ? matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  function quieto() { return !g || reducido.matches; }
  function todos(raiz, sel) { return [].slice.call(raiz.querySelectorAll(sel)); }
  var LIMPIA = "transform,opacity";

  var M = {};
  M.quieto = quieto;

  /* ---------- Lo que hay que medir antes de repintar ---------- */
  M.antes = function (raiz) {
    var barra = raiz.querySelector(".progreso i");
    var marcas = todos(raiz, "[data-flip-id]");
    return {
      pct: barra ? barra.style.width : null,
      flip: !quieto() && F && marcas.length ? F.getState(marcas) : null
    };
  };

  /* ---------- Lo que se anima después de repintar ----------
     tipo: "entrar" (pantalla nueva), "adelante" / "atras" (otra pregunta), "pestana" (otra pestaña de inicio),
     "plegar" (enunciado del supuesto) o nada (refresco de la misma pantalla). */
  M.despues = function (raiz, tipo, antes) {
    if (quieto()) return;
    antes = antes || {};
    var barra = raiz.querySelector(".progreso i");
    if (barra) {
      if (antes.pct && antes.pct !== barra.style.width) g.fromTo(barra, { width: antes.pct }, { width: barra.style.width, duration: 0.4, ease: "power2.out" });
      else if (tipo === "entrar") g.from(barra, { width: 0, duration: 0.5, delay: 0.1, ease: "power2.out" });
    }
    if (tipo === "entrar") entrada(raiz);
    else if (tipo === "adelante" || tipo === "atras") pregunta(raiz);
    else if (tipo === "pestana") pestana(raiz);
    else if (tipo === "plegar") plegar(raiz, antes.flip);
  };

  /* Pantalla nueva: los bloques entran uno detrás de otro, con un pequeño desplazamiento. */
  function entrada(raiz) {
    var bloques = todos(raiz, ".pagina > *, .fija > *, .res-cols > *");
    bloques = bloques.filter(function (b) { return !b.classList.contains("res-cols") && !b.hidden; });
    if (!bloques.length) return;
    g.from(bloques, { opacity: 0, y: 12, duration: 0.3, stagger: 0.04, ease: "power2.out", clearProps: LIMPIA });
    if (raiz.querySelector(".marcador")) resultados(raiz);
  }

  /* Otra pregunta: la tarjeta blanca no se mueve. Su contenido se apaga (0,1 s) y el nuevo aparece entero de una vez,
     subiendo un poco. Sin desplazamiento lateral ni opciones escalonadas: eran dos movimientos seguidos y parecía un carrusel. */
  function pregunta(raiz) {
    var c = raiz.querySelector(".tarjeta-cuerpo"); if (!c) return;
    g.from(c, { y: 6, opacity: 0, duration: 0.22, ease: "power2.out", clearProps: LIMPIA });
  }
  M.salida = function (el, dir, hecho) {
    if (quieto() || !el) return hecho();
    g.to(el, { opacity: 0, duration: 0.1, ease: "power1.in", onComplete: hecho });
  };

  /* Pestañas de inicio: el cambio es inmediato. El fondo blanco aparece en la pestaña nueva con un pequeño crecimiento
     y el contenido de abajo se funde a la vez. Los textos cambian de color con la misma duración (estilos.css). */
  function pestana(raiz) {
    var marca = raiz.querySelector(".pestana-marca");
    if (marca) g.from(marca, { opacity: 0, scale: 0.92, duration: 0.18, ease: "power2.out", clearProps: LIMPIA });
    g.from(todos(raiz, ".pestanas ~ *"), { opacity: 0, duration: 0.18, ease: "power1.out", clearProps: "opacity" });
  }

  /* Plegar o mostrar el enunciado del supuesto: las dos zonas cambian de tamaño en lugar de saltar. */
  function plegar(raiz, estado) {
    if (estado && F) F.from(estado, { targets: todos(raiz, "[data-flip-id]"), duration: 0.3, ease: "power2.inOut" });
    var texto = raiz.querySelector(".caso-texto");
    if (texto) g.from(texto, { opacity: 0, duration: 0.25, delay: 0.1, clearProps: "opacity" });
  }

  /* ---------- Al responder ---------- */
  M.respuesta = function (caja) {
    if (quieto() || !caja) return;
    var bien = caja.querySelector(".opcion.bien"), mal = caja.querySelector(".opcion.mal");
    if (bien) g.fromTo(bien, { scale: 1 }, { scale: 1.02, duration: 0.12, yoyo: true, repeat: 1, ease: "power1.out", clearProps: "transform" });
    if (mal) g.to(mal, { keyframes: { x: [0, -4, 4, -4, 4, 0] }, duration: 0.28, ease: "none", clearProps: "transform" });
    g.from(todos(caja, ".marca"), { scale: 0, transformOrigin: "50% 50%", duration: 0.3, ease: "back.out(2)", clearProps: "transform" });
  };

  /* ---------- Acordeones: se abren y se cierran por altura ---------- */
  var CAJA = "height,paddingTop,paddingBottom,opacity,overflow";
  M.abrir = function (el) {
    if (!el) return;
    if (g) g.killTweensOf(el);
    el.hidden = false;
    if (quieto()) return;
    g.set(el, { clearProps: CAJA });
    g.from(el, { height: 0, paddingTop: 0, paddingBottom: 0, opacity: 0, overflow: "hidden", duration: 0.25, ease: "power2.out", clearProps: CAJA });
  };
  M.cerrar = function (el) {
    if (!el) return;
    if (g) g.killTweensOf(el);
    if (quieto()) { el.hidden = true; return; }
    g.to(el, { height: 0, paddingTop: 0, paddingBottom: 0, opacity: 0, overflow: "hidden", duration: 0.2, ease: "power2.in",
      onComplete: function () { el.hidden = true; g.set(el, { clearProps: CAJA }); } });
  };

  /* ---------- Diálogos y visor ---------- */
  M.dialogoEntra = function (d, conEscala) {
    if (!d) return;
    if (g) { g.killTweensOf(d); g.set(d, { clearProps: LIMPIA }); }
    d.classList.remove("cerrando");
    if (quieto()) return;
    /* El visor gira con transform en el móvil de pie: ahí solo se funde, sin escala. */
    g.from(d, conEscala ? { opacity: 0, scale: 0.96, duration: 0.18, ease: "power2.out", clearProps: LIMPIA }
                        : { opacity: 0, duration: 0.18, ease: "power2.out", clearProps: "opacity" });
  };
  M.dialogoSale = function (d, conEscala, cerrar) {
    if (!d || quieto() || !d.open) return cerrar();
    g.killTweensOf(d);
    d.classList.add("cerrando");
    g.to(d, { opacity: 0, scale: conEscala ? 0.97 : 1, duration: 0.12, ease: "power1.in",
      onComplete: function () { cerrar(); d.classList.remove("cerrando"); g.set(d, { clearProps: LIMPIA }); } });
  };

  /* ---------- Resultados ---------- */
  function contar(el, hasta, decimales) {
    var o = { v: 0 };
    function texto(v) { return decimales ? v.toFixed(decimales).replace(".", ",") : String(Math.round(v)); }
    el.textContent = texto(0);
    g.to(o, { v: hasta, duration: 0.6, delay: 0.15, ease: "power2.out", onUpdate: function () { el.textContent = texto(o.v); },
      onComplete: function () { el.textContent = texto(hasta); } });
  }
  function resultados(raiz) {
    todos(raiz, ".dato b").forEach(function (b) { contar(b, parseInt(b.textContent, 10) || 0, 0); });
    var neta = raiz.querySelector(".neta b");
    if (neta) contar(neta, parseFloat(neta.textContent.replace(",", ".")) || 0, 2);
    /* Las barras de "Cómo vas por temas" crecen cuando el panel llega a la vista: está al final y, si no, se animarían sin que nadie las viera. */
    var est = raiz.querySelector(".estadistica");
    if (!est || !window.IntersectionObserver) return;
    var anim = g.from(todos(est, ".barra i"), { width: 0, duration: 0.6, stagger: 0.015, ease: "power2.out", paused: true });
    var io = new IntersectionObserver(function (e) {
      if (!e[0].isIntersecting) return;
      io.disconnect(); anim.play();
    }, { threshold: 0.1 });
    io.observe(est);
  }

  /* Al saltar a una pregunta desde "Ir a una pregunta", se marca un momento para ver dónde has caído. */
  M.resaltar = function (el) {
    if (!el) return;
    el.classList.remove("resaltado");
    setTimeout(function () { el.classList.add("resaltado"); }, quieto() ? 0 : 350);
    setTimeout(function () { el.classList.remove("resaltado"); }, quieto() ? 1500 : 1300);
  };

  window.Mov = M;
})();
