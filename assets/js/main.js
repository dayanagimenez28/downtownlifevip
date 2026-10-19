// Navegación: al ir hacia delante la página empieza arriba; al volver atrás
// (con el botón "Volver" o con la flecha del navegador) recupera el punto donde estabas.
(function () {
  var KEY = 'pos:' + location.pathname;
  function get(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
  function del(k) { try { sessionStorage.removeItem(k); } catch (e) {} }
  try { if ('scrollRestoration' in history) history.scrollRestoration = 'manual'; } catch (e) {}

  function save() { set(KEY, String(window.scrollY || window.pageYOffset || 0)); }
  var t;
  window.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(save, 120); }, { passive: true });
  window.addEventListener('pagehide', save);

  var nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {};
  var goingBack = nav.type === 'back_forward' || get('volver') === '1';
  del('volver');

  function apply() {
    if (location.hash) return;
    var y = goingBack ? parseInt(get(KEY) || '0', 10) : 0;
    window.scrollTo({ top: y, left: 0, behavior: 'instant' });
  }
  apply();
  document.addEventListener('DOMContentLoaded', apply);
  window.addEventListener('load', function () { if (goingBack) apply(); });
  window.addEventListener('pageshow', function (e) { if (e.persisted) { goingBack = true; apply(); } });

  // Botón "Volver"
  Array.prototype.forEach.call(document.querySelectorAll('[data-back]'), function (a) {
    a.addEventListener('click', function (e) {
      save();
      set('volver', '1');
      var ref = null;
      try { ref = document.referrer ? new URL(document.referrer) : null; } catch (err) {}
      if (ref && ref.host === location.host && history.length > 1) { e.preventDefault(); history.back(); }
    });
  });
})();



// Downtown Life VIP — menú móvil y visor de fotos
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  var links = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
  if (!links.length) return;
  var box = document.createElement('div');
  box.className = 'lightbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', 'Fotos del apartamento');
  box.innerHTML = '<button class="lb-close" type="button">Cerrar ✕</button>' +
    '<button class="lb-prev" type="button" aria-label="Foto anterior">‹</button>' +
    '<img alt="">' +
    '<button class="lb-next" type="button" aria-label="Foto siguiente">›</button>' +
    '<div class="lb-count"></div>';
  document.body.appendChild(box);
  var img = box.querySelector('img'), count = box.querySelector('.lb-count'), cur = 0, last = null;

  function show(i) {
    cur = (i + links.length) % links.length;
    img.src = links[cur].getAttribute('href');
    img.alt = (links[cur].querySelector('img') || {}).alt || '';
    count.textContent = (cur + 1) + ' / ' + links.length;
    box.classList.add('open');
  }
  function close() { box.classList.remove('open'); if (last) last.focus(); }

  links.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); last = a; show(i); box.querySelector('.lb-close').focus(); });
  });
  box.querySelector('.lb-close').addEventListener('click', close);
  box.querySelector('.lb-prev').addEventListener('click', function (e) { e.stopPropagation(); show(cur - 1); });
  box.querySelector('.lb-next').addEventListener('click', function (e) { e.stopPropagation(); show(cur + 1); });
  box.addEventListener('click', function (e) { if (e.target === box) close(); });
  document.addEventListener('keydown', function (e) {
    if (!box.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') show(cur + 1);
    if (e.key === 'ArrowLeft') show(cur - 1);
  });
})();

// WhatsApp: en móvil abre la app; en ordenador muestra un código QR para escanear con el móvil
(function () {
  var modal = document.getElementById('wa-modal');
  if (!modal) return;
  var isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
    (navigator.maxTouchPoints > 1 && /Macintosh/.test(navigator.userAgent));
  if (isMobile) return;
  var last = null;
  function close() { modal.hidden = true; if (last) last.focus(); }
  Array.prototype.forEach.call(document.querySelectorAll('[data-wa]'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); last = a; modal.hidden = false;
      modal.querySelector('.wa-modal-x').focus();
    });
  });
  modal.querySelector('.wa-modal-x').addEventListener('click', close);
  modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) close(); });
})();



// Portada: las fotos cambian solas en orden aleatorio cada 6 segundos (fundido suave)
(function () {
  var box = document.querySelector('[data-slideshow]');
  if (!box) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var imgs = Array.prototype.slice.call(box.querySelectorAll('img'));
  if (imgs.length < 2) return;
  function load(im) {
    if (im.dataset.src) {
      if (im.dataset.srcset) im.srcset = im.dataset.srcset;
      im.src = im.dataset.src;
      im.removeAttribute('data-src'); im.removeAttribute('data-srcset');
    }
  }
  var current = 0, order = [];
  function shuffle() {
    order = imgs.map(function (_, i) { return i; }).filter(function (i) { return i !== current; });
    for (var i = order.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = order[i]; order[i] = order[j]; order[j] = t; }
  }
  function next() {
    if (!order.length) shuffle();
    var n = order.shift(), im = imgs[n];
    load(im);
    var show = function () {
      imgs[current].classList.remove('is-active'); im.classList.add('is-active'); current = n;
      if (order.length) load(imgs[order[0]]);
    };
    if (im.complete && im.naturalWidth) show(); else im.addEventListener('load', show, { once: true });
  }
  window.addEventListener('load', function () {
    shuffle(); load(imgs[order[0]]);
    setInterval(function () { if (!document.hidden) next(); }, 6000);
  });
})();

// Botón "Compartir": en el móvil abre el menú de compartir del teléfono (como TikTok);
// si no está disponible, muestra opciones (WhatsApp, Facebook, Telegram, X y copiar enlace).
(function () {
  var box = document.querySelector('[data-share]');
  if (!box) return;
  var d = box.dataset, btn = box.querySelector('[data-share-btn]'), menu = box.querySelector('.share-menu');
  function toggle(open) { menu.hidden = !open; btn.setAttribute('aria-expanded', String(open)); }
  btn.addEventListener('click', function () {
    if (navigator.share) {
      navigator.share({ title: d.title, url: d.url }).catch(function (err) {
        if (!err || err.name !== 'AbortError') toggle(menu.hidden);
      });
    } else { toggle(menu.hidden); }
  });
  document.addEventListener('click', function (e) { if (!box.contains(e.target)) toggle(false); });
  box.querySelector('[data-share-copy]').addEventListener('click', function () {
    var sp = this.querySelector('span'), old = sp.textContent;
    var ok = function () { sp.textContent = d.copied; setTimeout(function () { sp.textContent = old; }, 2000); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(d.url).then(ok, function () { window.prompt('', d.url); });
    } else { window.prompt('', d.url); }
  });
})();

// Comodidades: se muestran plegadas y se abren con un botón
(function () {
  var w = document.querySelector('[data-collapse]');
  if (!w) return;
  var b = w.querySelector('[data-collapse-btn]'), label = b.textContent;
  b.addEventListener('click', function () {
    var open = w.classList.toggle('is-collapsed') === false;
    b.setAttribute('aria-expanded', String(open));
    b.textContent = open ? 'Ver menos' : label;
    if (!open) w.scrollIntoView({ block: 'start' });
  });
})();
