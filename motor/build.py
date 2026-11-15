# -*- coding: utf-8 -*-
"""Arma el informe "Tendencias en redes · Fútbol" a partir de una edición en JSON.
   python motor/build.py                      -> usa la edición más reciente de motor/ediciones/
   python motor/build.py motor/ediciones/2026-11-14.json
Escribe index.html (la edición actual) y ediciones/<fecha>.html (archivo de cada semana) en la raíz del repo.
Esquema de la edición: ver motor/INSTRUCCIONES.md. Todo texto visible va en {"es": ..., "en": ...}."""
import io, os, sys, json, glob, html
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ED = os.path.join(RAIZ, 'motor', 'ediciones')
E = html.escape

def cargar(ruta=None):
    if not ruta:
        ruta = sorted(glob.glob(os.path.join(ED, '*.json')))[-1]
    return json.load(io.open(ruta, encoding='utf-8')), ruta

def tx(v, l):
    """Texto en el idioma l. Acepta {"es","en"} o un valor simple."""
    if isinstance(v, dict):
        return v.get(l) or v.get('es') or ''
    return '' if v is None else str(v)

def num_veces(v, l):
    s = ('%g' % v) if isinstance(v, (int, float)) else str(v)
    return s.replace('.', ',') if l == 'es' else s

import datetime as _dt, urllib.parse as _up

def miami(iso):
    """UTC (ISO) -> hora de Miami con horario de verano de EE. UU. (2.º domingo de marzo a 1.er domingo de noviembre, 2 a. m.)."""
    u = _dt.datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(_dt.timezone.utc).replace(tzinfo=None)
    y = u.year
    mar = _dt.datetime(y, 3, 8); mar += _dt.timedelta(days=(6 - mar.weekday()) % 7)
    nov = _dt.datetime(y, 11, 1); nov += _dt.timedelta(days=(6 - nov.weekday()) % 7)
    verano = mar + _dt.timedelta(hours=7) <= u < nov + _dt.timedelta(hours=6)
    return u - _dt.timedelta(hours=4 if verano else 5)

MES = {'es': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
       'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}

def fecha_hora(d, l):
    h = d.hour % 12 or 12
    if l == 'es':
        return f'{d.day} {MES["es"][d.month - 1]} {d.year}, {h}:{d.minute:02d} {"a. m." if d.hour < 12 else "p. m."}'
    return f'{MES["en"][d.month - 1]} {d.day}, {d.year}, {h}:{d.minute:02d} {"AM" if d.hour < 12 else "PM"}'

def proxima(d):
    """Próximo lunes a las 7:30 (Miami) después de d."""
    p = d.replace(hour=7, minute=30, second=0, microsecond=0) + _dt.timedelta(days=(7 - d.weekday()) % 7)
    return p if p > d else p + _dt.timedelta(days=7)

def chispa(curva):
    """Mini gráfico SVG de la tendencia (popularidad de los últimos días)."""
    if not curva or len(curva) < 2:
        return ''
    mx = max(curva) or 1
    pts = ' '.join(f'{i * 80 / (len(curva) - 1):.1f},{24 - v / mx * 22:.1f}' for i, v in enumerate(curva))
    return f'<svg class="chispa" viewBox="0 0 80 26" width="80" height="26" aria-hidden="true"><polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></svg>'

def tag_url(h):
    return 'https://www.tiktok.com/tag/' + _up.quote(h.lstrip('#'))

def tabla(cols, filas):
    head = ''.join(f'<th>{E(c)}</th>' for c in cols)
    return f'<div class="tabla"><table><thead><tr>{head}</tr></thead><tbody>{"".join(filas)}</tbody></table></div>'

def cuerpo(d, l, otras):
    es = l == 'es'
    T = lambda a, b: a if es else b
    k = d.get('kpis', [])
    kpis = ''.join(f'<div class="kpi"><b>{E(x["valor"])}</b><span>{E(tx(x, l))}</span></div>' for x in k)
    hall = ''.join(f'<li>{tx(h, l)}</li>' for h in d.get('hallazgos', []))
    tt = d.get('tiktok', {})
    ver_v = T('Ver videos', 'See videos')
    def celda_tag(r):
        return (f'<td><a class="tag" href="{E(tag_url(r["hashtag"]))}" target="_blank" rel="noopener"><b>{E(r["hashtag"])}</b></a>'
                f'<div class="tagv"><a href="{E(tag_url(r["hashtag"]))}" target="_blank" rel="noopener">{ver_v} ↗</a></div></td>')
    hay_curva = any(r.get('curva') for r in tt.get('filas', []))
    filas_tt = [f'<tr><td class="n">{E(str(r.get("puesto", "")))}</td>{celda_tag(r)}<td>{E(tx(r.get("desc", ""), l))}</td>'
                + (f'<td>{chispa(r.get("curva"))}</td>' if hay_curva else '') +
                f'<td class="n">{E(str(r.get("videos", "")))}</td><td class="n">{E(str(r.get("vistas", "")))}</td></tr>' for r in tt.get('filas', [])]
    con_desc = any(r.get('desc') for r in tt.get('formatos', []))
    filas_fm = [f'<tr><td class="n">{E(str(r.get("puesto", "")))}</td>{celda_tag(r)}' + (f'<td>{E(tx(r.get("desc", ""), l))}</td>' if con_desc else '') +
                f'<td class="n">{E(str(r.get("videos", "")))}</td><td class="n">{E(str(r.get("vistas", "")))}</td></tr>' for r in tt.get('formatos', [])]
    c_base = T(['Puesto', 'Hashtag', 'De qué es', 'Videos', 'Vistas'], ['Rank', 'Hashtag', 'What it is', 'Videos', 'Views'])
    c_tt = c_base[:3] + ([T('Tendencia 7 días', '7-day trend')] if hay_curva else []) + c_base[3:]
    c_fm = c_base if con_desc else [c for c in c_base if c not in ('De qué es', 'What it is')]
    bloque_tt = ''
    if filas_tt:
        bloque_tt += tabla(c_tt, filas_tt)
    if filas_fm:
        bloque_tt += f'<h3 class="sub">{E(tx(tt.get("formatos_titulo", {"es": "Retos y formatos", "en": "Challenges and formats"}), l))}</h3>'
        if tt.get('formatos_nota'):
            bloque_tt += f'<p class="lead">{E(tx(tt["formatos_nota"], l))}</p>'
        bloque_tt += tabla(c_fm, filas_fm)
    if tt.get('nota_final'):
        bloque_tt += f'<p class="lead" style="margin-top:12px">{E(tx(tt["nota_final"], l))}</p>'
    ig = d.get('instagram', {})
    ver = T('Abrir', 'Open')
    veces_t = T('veces lo normal', 'times usual')
    tarjetas_ig = ''.join(
        f'<article class="igc"><div class="igc-cab"><b class="igc-x">{E(num_veces(r["veces"], l))}×</b><span class="igc-xl">{veces_t}</span>'
        f'<span class="igc-f">{E(tx(r["formato"], l))}</span></div>'
        f'<div class="igc-c">@{E(r["cuenta"])}</div><p class="igc-q">{E(tx(r["que"], l))}</p>'
        f'<div class="igp" data-ig="{E(r["enlace"])}"><a class="igp-f" href="{E(r["enlace"])}" target="_blank" rel="noopener">{T("Cargando vista previa…", "Loading preview…")}</a></div>'
        f'<a class="igc-a" href="{E(r["enlace"])}" target="_blank" rel="noopener">{T("Abrir en Instagram", "Open on Instagram")} ↗</a></article>'
        for r in ig.get('filas', []))
    pat = ''.join(f'<div class="panel"><h3>{E(tx(p["titulo"], l))}</h3><p>{E(tx(p["texto"], l))}</p></div>' for p in d.get('patrones', []))
    ideas = ''.join(f'<div class="panel"><h3>{E(cta)}</h3><ul>{"".join(f"<li>{E(tx(i, l))}</li>" for i in lst)}</ul></div>' for cta, lst in d.get('ideas', {}).items())
    met = ''.join(f'<li>{tx(m, l)}</li>' for m in d.get('metodo', []))
    nuestras = d.get('nuestras', {})
    bloque_nuestras = ''
    if nuestras.get('filas'):
        c_n = T(['Cuenta', 'Seguidores', 'Publicaciones leídas', 'Me gusta (mediana)', 'Lo mejor de la semana'], ['Account', 'Followers', 'Posts read', 'Likes (median)', 'Best of the week'])
        filas_n = [f'<tr><td>@{E(r["cuenta"])}</td><td class="n">{E(str(r.get("seguidores", "")))}</td><td class="n">{E(str(r.get("posts", "")))}</td>'
                   f'<td class="n">{E(str(r.get("mediana", "")))}</td><td>{E(tx(r.get("mejor", ""), l))}</td></tr>' for r in nuestras['filas']]
        bloque_nuestras = f'''<section id="{l}-nuestras"><h2>{T('Nuestras cuentas', 'Our accounts')}</h2><p class="lead">{E(tx(nuestras.get("nota", ""), l))}</p>{tabla(c_n, filas_n)}</section>'''
    arch = ''
    if otras:
        arch = '<section><h2>' + T('Ediciones anteriores', 'Past editions') + '</h2><ul>' + ''.join(
            f'<li><a href="{E(h)}?lang={l}">{E(t)}</a></li>' for t, h in otras) + '</ul></section>'
    nav = [('minuto', T('En 1 minuto', 'In 1 minute')), ('tiktok', 'TikTok'), ('instagram', 'Instagram')]
    if bloque_nuestras:
        nav.append(('nuestras', T('Nuestras cuentas', 'Our accounts')))
    nav += [('patrones', T('Qué se repite', 'Patterns')), ('ideas', T('Ideas por cuenta', 'Ideas by account')), ('metodo', T('Método', 'Method'))]
    navh = ''.join(f'<a href="#{l}-{a}">{b}</a>' for a, b in nav)
    return f'''
<nav><div class="in">{navh}</div></nav>
<main>
<section id="{l}-minuto"><h2>{T('En 1 minuto', 'In 1 minute')}</h2>
  <p class="lead">{E(tx(d.get("intro", ""), l))}</p>
  <div class="kpis">{kpis}</div><ol class="hall">{hall}</ol></section>
<section id="{l}-tiktok"><h2>{E(tx(tt.get("titulo", "TikTok"), l))}</h2><p class="lead">{E(tx(tt.get("fuente", ""), l))}</p>{bloque_tt}</section>
<section id="{l}-instagram"><h2>{E(tx(ig.get("titulo", "Instagram"), l))}</h2><p class="lead">{E(tx(ig.get("nota", ""), l))}</p><div class="igs">{tarjetas_ig}</div></section>
{bloque_nuestras}
<section id="{l}-patrones"><h2>{T('Qué se repite', 'Patterns')}</h2><div class="grid">{pat}</div></section>
<section id="{l}-ideas"><h2>{T('Ideas por cuenta', 'Ideas by account')}</h2>
  <p class="lead">{T('Puntos para revisar con el equipo; no son una decisión tomada. Con menores, siempre con autorización de las familias.', 'Points to review with the team, not a final decision. With minors, always with family consent.')}</p>
  <div class="grid">{ideas}</div></section>
<section id="{l}-metodo"><h2>{T('Cómo se hizo y cada cuánto se actualiza', 'How it was made and how often it updates')}</h2><ul>{met}</ul></section>
{arch}
</main>'''

CSS = '''
:root{--bg:#f6f5f2;--panel:#fff;--panel2:#f1efea;--ink:#16161a;--suave:#5d5b57;--linea:#e2dfd8;--oro:#b9873a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121214;--panel:#1b1b1f;--panel2:#24242a;--ink:#f1efe9;--suave:#a9a6a0;--linea:#2f2f36;--oro:#d4a457}}
:root[data-theme=dark]{--bg:#121214;--panel:#1b1b1f;--panel2:#24242a;--ink:#f1efe9;--suave:#a9a6a0;--linea:#2f2f36;--oro:#d4a457}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{background:#111;color:#f4f1ea;padding:28px 16px 22px}
header .in,main{max-width:1180px;margin:0 auto}
header h1{margin:0;font-size:clamp(22px,3.4vw,32px)}header h1 span{color:var(--oro)}
header p{margin:6px 0 0;color:#c9c5bd;font-size:14px}
.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}
.idioma{display:flex;border:1px solid #3a3a3a;border-radius:99px;overflow:hidden}
.idioma button{background:none;border:0;color:#d8d4cc;font:600 13px system-ui;padding:6px 12px;cursor:pointer}
.idioma button[aria-pressed=true]{background:var(--oro);color:#111}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.chip{border:1px solid #3a3a3a;border-radius:99px;padding:3px 11px;font-size:12.5px;color:#d8d4cc}
nav{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--linea);overflow-x:auto;white-space:nowrap}
nav .in{max-width:1180px;margin:0 auto;padding:0 10px}
nav a{display:inline-block;padding:11px 10px;color:var(--suave);text-decoration:none;font-size:13.5px;font-weight:600}nav a:hover{color:var(--ink)}
main{padding:8px 16px 60px}section{margin-top:34px;scroll-margin-top:50px}
h2{font-size:21px;margin:0 0 4px}h3{font-size:16px;margin:0 0 6px}h3.sub{margin:22px 0 4px}
.lead{color:var(--suave);margin:0 0 14px;font-size:14px}
.panel{background:var(--panel);border:1px solid var(--linea);border-radius:12px;padding:16px}.panel p{margin:0}.panel ul{margin:0;padding-left:18px}.panel li{margin-bottom:6px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.kpis{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));margin-bottom:18px}
.kpi{background:var(--panel);border:1px solid var(--linea);border-radius:12px;padding:14px}
.kpi b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}.kpi span{color:var(--suave);font-size:13px}
ol.hall{margin:0;padding-left:20px}ol.hall li{margin:0 0 10px}
.tabla{overflow-x:auto;border:1px solid var(--linea);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--linea);vertical-align:top}
th{background:var(--panel2);font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--suave);white-space:nowrap}
tr:last-child td{border-bottom:0}td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:var(--oro)}
footer{max-width:1180px;margin:0 auto;padding:0 16px 40px;color:var(--suave);font-size:12.5px}
[data-l]{display:none}html[lang=es] [data-l=es],html[lang=en] [data-l=en]{display:block}
.upd{display:flex;flex-wrap:wrap;gap:6px 22px;margin-top:12px;font-size:13px;color:#c9c5bd}.upd b{color:#f4f1ea;font-weight:600}
a.tag{color:var(--ink);text-decoration:none}a.tag:hover{text-decoration:underline}.tagv{font-size:12px;margin-top:2px}.tagv a{color:var(--oro);text-decoration:none}
.chispa{color:var(--oro);display:block}
.igs{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));align-items:start}
.igc{background:var(--panel);border:1px solid var(--linea);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:6px;min-width:0}
.igc-cab{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.igc-x{font-size:24px;font-variant-numeric:tabular-nums}.igc-xl{font-size:12.5px;color:var(--suave)}
.igc-f{margin-left:auto;font-size:12px;border:1px solid var(--linea);border-radius:99px;padding:2px 9px;color:var(--suave)}
.igc-c{font-weight:700;font-size:14px}.igc-q{margin:0;font-size:13.5px;color:var(--suave)}
.igp{min-height:120px;border-radius:10px;overflow:hidden;background:var(--panel2);display:flex;justify-content:center}
.igp-f{align-self:center;font-size:13px;color:var(--suave);padding:20px;text-decoration:none}
.igp .instagram-media{margin:0!important;min-width:0!important;width:100%!important;max-width:540px!important;border:0!important}
.igc-a{font-size:13px;color:var(--oro);text-decoration:none;font-weight:600}
'''

def cabecera(d, l):
    es = l == 'es'
    ed = (f'Edición {d["numero"]}' if es else f'Edition {d["numero"]}') + ' · ' + tx(d['fecha_texto'], l)
    act = d.get('actualizado')
    if act:
        m = miami(act)
        upd = (f'<div class="upd"><span><b>{"Última actualización" if es else "Last update"}:</b> {E(fecha_hora(m, l))} (Miami)</span>'
               f'<span><b>{"Próxima" if es else "Next"}:</b> <span data-prox>{E(fecha_hora(proxima(m), l))}</span> (Miami)</span></div>')
    else:
        upd = ''
    return f'''<header><div class="in"><div class="top"><div>
<h1>{'Tendencias en redes' if es else 'Social media trends'} · <span>{'Fútbol' if es else 'Soccer'}</span></h1>
<p>{'Qué se está viralizando alrededor del fútbol para aplicarlo en Athletum, Juve Miami y Juventus Camps.' if es else 'What is going viral around soccer, to apply at Athletum, Juve Miami and Juventus Camps.'}</p></div>
<div class="idioma" role="group" aria-label="Idioma / Language"><button type="button" data-set="es">ES</button><button type="button" data-set="en">EN</button></div></div>
<div class="chips"><span class="chip">{E(ed)}</span><span class="chip">TikTok · Instagram</span><span class="chip">{'Se actualiza cada lunes de forma automática' if es else 'Updated automatically every Monday'}</span></div>
{upd}
</div></header>'''

def pagina(d, otras, pref=''):
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Tendencias en redes · Fútbol</title>
<meta name="description" content="Qué se está viralizando alrededor del fútbol en TikTok e Instagram, cada semana.">
<meta property="og:title" content="Social media trends · Soccer"><meta property="og:description" content="Weekly: what is going viral around soccer on TikTok and Instagram.">
<link rel="icon" type="image/svg+xml" href="{pref}favicon.svg"><meta name="theme-color" content="#111111">
<style>{CSS}</style>
</head>
<body>
<div data-l="es">{cabecera(d, 'es')}{cuerpo(d, 'es', otras)}</div>
<div data-l="en">{cabecera(d, 'en')}{cuerpo(d, 'en', otras)}</div>
<footer><span data-l="es">Soccer Cage LLC · Marketing</span><span data-l="en">Soccer Cage LLC · Marketing</span></footer>
<script>
(function(){{
  function elegir(){{
    try{{var q=new URLSearchParams(location.search).get('lang');if(q==='es'||q==='en')return q;}}catch(e){{}}
    try{{var g=localStorage.getItem('sc-lang');if(g==='es'||g==='en')return g;}}catch(e){{}}
    var n=(navigator.languages&&navigator.languages[0])||navigator.language||'es';return /^en/i.test(n)?'en':'es';
  }}
  function poner(l){{document.documentElement.lang=l;document.title=l==='en'?'Social media trends · Soccer':'Tendencias en redes · Fútbol';
    document.querySelectorAll('.idioma button').forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.set===l?'true':'false');}});}}
  // Vistas previas de Instagram: se cargan solo en el idioma visible y cuando la tarjeta entra en pantalla.
  var igListo=false,igCola=[];
  function igScript(cb){{if(window.instgrm){{cb();return;}}igCola.push(cb);if(igListo)return;igListo=true;var s=document.createElement('script');s.async=true;s.src='https://www.instagram.com/embed.js';
    s.onload=function(){{igCola.splice(0).forEach(function(f){{f();}});}};document.body.appendChild(s);}}
  var obs=('IntersectionObserver' in window)?new IntersectionObserver(function(es){{es.forEach(function(en){{if(en.isIntersecting){{obs.unobserve(en.target);cargar(en.target);}}}});}},{{rootMargin:'400px'}}):null;
  function cargar(el){{if(el.dataset.ok)return;el.dataset.ok='1';var u=el.dataset.ig.split('?')[0];
    el.innerHTML='<blockquote class="instagram-media" data-instgrm-permalink="'+u+'?utm_source=ig_embed" data-instgrm-version="14"></blockquote>';
    igScript(function(){{window.instgrm.Embeds.process();}});}}
  function vigilar(){{var l=document.documentElement.lang;document.querySelectorAll('[data-l="'+l+'"] .igp[data-ig]').forEach(function(el){{if(el.dataset.ok)return;if(obs)obs.observe(el);else cargar(el);}});}}
  poner(elegir());vigilar();
  document.querySelectorAll('.idioma button').forEach(function(b){{b.onclick=function(){{poner(b.dataset.set);vigilar();try{{localStorage.setItem('sc-lang',b.dataset.set);}}catch(e){{}}}};}});
}})();
</script>
</body></html>'''

def main():
    d, ruta = cargar(sys.argv[1] if len(sys.argv) > 1 else None)
    todas = sorted(glob.glob(os.path.join(ED, '*.json')))
    os.makedirs(os.path.join(RAIZ, 'ediciones'), exist_ok=True)
    # archivo de cada edición (incluida la actual)
    for r in todas:
        e = json.load(io.open(r, encoding='utf-8'))
        io.open(os.path.join(RAIZ, 'ediciones', e['fecha'] + '.html'), 'w', encoding='utf-8').write(pagina(e, [], '../'))
    otras = [(f'Edición {json.load(io.open(r, encoding="utf-8"))["numero"]} · {os.path.basename(r)[:-5]}', 'ediciones/' + os.path.basename(r)[:-5] + '.html')
             for r in reversed(todas) if os.path.abspath(r) != os.path.abspath(ruta)]
    io.open(os.path.join(RAIZ, 'index.html'), 'w', encoding='utf-8').write(pagina(d, otras))
    print('ok', os.path.basename(ruta), '| ediciones:', len(todas))

if __name__ == '__main__':
    main()
