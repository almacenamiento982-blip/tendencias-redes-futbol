# -*- coding: utf-8 -*-
"""Arma el informe "Tendencias en redes · Fútbol" a partir de una edición en JSON (formato v2, 15-11-2026).
   python motor/build.py                      -> usa la edición más reciente de motor/ediciones/
Escribe index.html (edición actual) y ediciones/<fecha>.html en la raíz del repo.
Línea gráfica del command center (soccercage-marketing.pages.dev): fondo oscuro, acento lima, Inter.
Objetivo (David, 15-11): que se entienda desde el inicio qué tendencias hay y cuáles replicar, sin tanto detalle.
Esquema: ver motor/INSTRUCCIONES.md. Todo texto visible va en {"es": ..., "en": ...}."""
import io, os, sys, json, glob, html
import datetime as _dt, urllib.parse as _up
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ED = os.path.join(RAIZ, 'motor', 'ediciones')
E = html.escape
CUENTAS = ['Athletum', 'Juve Miami', 'Juventus Camps']

def tx(v, l):
    if isinstance(v, dict):
        return v.get(l) or v.get('es') or ''
    return '' if v is None else str(v)

# ---------- fechas en hora de Miami ----------
def miami(iso):
    u = _dt.datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(_dt.timezone.utc).replace(tzinfo=None)
    y = u.year
    mar = _dt.datetime(y, 3, 8); mar += _dt.timedelta(days=(6 - mar.weekday()) % 7)
    nov = _dt.datetime(y, 11, 1); nov += _dt.timedelta(days=(6 - nov.weekday()) % 7)
    verano = mar + _dt.timedelta(hours=7) <= u < nov + _dt.timedelta(hours=6)
    return u - _dt.timedelta(hours=4 if verano else 5)

MES = {'es': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
       'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
DIA = {'es': ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'], 'en': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

def fecha_hora(d, l):
    h = d.hour % 12 or 12
    if l == 'es':
        return f'{DIA["es"][d.weekday()]} {d.day} {MES["es"][d.month - 1]}, {h}:{d.minute:02d} {"a. m." if d.hour < 12 else "p. m."}'
    return f'{DIA["en"][d.weekday()]}, {MES["en"][d.month - 1]} {d.day}, {h}:{d.minute:02d} {"AM" if d.hour < 12 else "PM"}'

def proxima(d):
    p = d.replace(hour=7, minute=30, second=0, microsecond=0) + _dt.timedelta(days=(7 - d.weekday()) % 7)
    return p if p > d else p + _dt.timedelta(days=7)

def chispa(curva):
    if not curva or len(curva) < 2:
        return ''
    mx = max(curva) or 1
    pts = ' '.join(f'{i * 90 / (len(curva) - 1):.1f},{26 - v / mx * 24:.1f}' for i, v in enumerate(curva))
    return f'<svg class="chispa" viewBox="0 0 90 28" width="90" height="28" aria-hidden="true"><polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/></svg>'

def tag_url(h):
    return 'https://www.tiktok.com/tag/' + _up.quote(h.lstrip('#'))

def vistas_cortas(v, l):
    try:
        n = float(str(v).replace(',', ''))
    except ValueError:
        return str(v)
    if n >= 1e9: s = f'{n / 1e9:.1f} B' if l == 'en' else f'{n / 1e9:.1f} mil M'
    elif n >= 1e6: s = f'{n / 1e6:.0f} M'
    elif n >= 1e3: s = f'{n / 1e3:.0f} K' if l == 'en' else f'{n / 1e3:.0f} mil'
    else: s = f'{n:.0f}'
    return s.replace('.', ',') if l == 'es' else s

def corto(n, l):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return ''
    if n >= 1e6: s = f'{n / 1e6:.1f}'.rstrip('0').rstrip('.') + (' M' if l == 'es' else 'M')
    elif n >= 1e4: s = f'{n / 1e3:.0f}' + (' mil' if l == 'es' else 'K')
    elif n >= 1e3: s = f'{n / 1e3:.1f}'.rstrip('0').rstrip('.') + (' mil' if l == 'es' else 'K')
    else: s = f'{n:.0f}'
    return s.replace('.', ',') if l == 'es' else s

def cifras(x, l):
    """'732 mil reproducciones · 5,1 mil me gusta · 26 comentarios' (lo que haya)."""
    p = []
    if x.get('vistas'): p.append(corto(x['vistas'], l) + (' reproducciones' if l == 'es' else ' plays'))
    if x.get('likes') is not None: p.append(corto(x['likes'], l) + (' me gusta' if l == 'es' else ' likes'))
    if x.get('comentarios'): p.append(corto(x['comentarios'], l) + (' comentarios' if l == 'es' else ' comments'))
    return ' · '.join(p)

def chip_cuenta(c):
    return f'<span class="cta cta-{["athletum", "juve-miami", "juventus-camps"][CUENTAS.index(c)] if c in CUENTAS else "otra"}">{E(c)}</span>'

def preview(enlace, l):
    return (f'<div class="igp" data-ig="{E(enlace)}"><a class="igp-f" href="{E(enlace)}" target="_blank" rel="noopener">'
            f'{"Cargando vista previa…" if l == "es" else "Loading preview…"}</a></div>')

# ---------- secciones ----------
def cuerpo(d, l, otras):
    es = l == 'es'
    T = lambda a, b: a if es else b
    tends = d.get('tendencias', [])
    # 1. En pocas palabras: resumen + qué replicar por cuenta
    por_cuenta = {c: [] for c in CUENTAS}
    for i, t in enumerate(tends, 1):
        for r in t.get('replicar', []):
            if r.get('cuenta') in por_cuenta:
                por_cuenta[r['cuenta']].append((i, tx(r, l)))
    rep = ''.join(
        f'<div class="rep"><div class="rep-cab">{chip_cuenta(c)}</div><ul>' +
        ''.join(f'<li><span class="rep-n">{i}</span>{E(t)}</li>' for i, t in v[:3]) + '</ul></div>'
        for c, v in por_cuenta.items() if v)
    lista_t = ''.join(f'<li><a href="#{l}-t{i}"><span class="tn">{i}</span>{E(tx(t["titulo"], l))}</a></li>' for i, t in enumerate(tends, 1))
    s1 = f'''<section id="{l}-resumen"><div class="hero panel">
  <p class="eyebrow">{T('En pocas palabras', 'In a nutshell')}</p>
  <p class="hero-t">{E(tx(d.get("resumen", ""), l))}</p>
  <ol class="tlist">{lista_t}</ol></div>
  <h2>{T('Qué replicar esta semana', 'What to replicate this week')}</h2>
  <p class="sub">{T('El número indica la tendencia de la que sale cada idea.', 'The number shows the trend each idea comes from.')}</p>
  <div class="reps">{rep}</div></section>'''
    # 2. Tendencias
    cards = ''
    for i, t in enumerate(tends, 1):
        ej = t.get('ejemplos', [])[:2]
        prevs = ''.join(f'<div class="ej"><div class="ej-c">@{E(x["cuenta"])}</div>{preview(x["enlace"], l)}<div class="ej-s">{E(cifras(x, l))}</div></div>' for x in ej)
        rpl = ''.join(f'<li>{chip_cuenta(r.get("cuenta", ""))}<span>{E(tx(r, l))}</span></li>' for r in t.get('replicar', []))
        orig = {'instagram': 'Instagram', 'tiktok': 'TikTok'}.get(t.get('origen', 'instagram'), 'Instagram')
        cards += f'''<article class="tend panel" id="{l}-t{i}">
  <div class="tend-cab"><span class="tn tn-g">{i}</span><div><h3>{E(tx(t["titulo"], l))}</h3><span class="orig">{orig}</span></div></div>
  <p class="tend-q">{E(tx(t.get("que_es", ""), l))}</p>
  <p class="dato"><b>{T('Por qué es tendencia', 'Why it is trending')}:</b> {E(tx(t.get("dato", ""), l))}</p>
  <div class="tend-body"><div class="ejs ejs-{len(ej)}">{prevs}</div>
  <div class="cmo"><p class="eyebrow">{T('Cómo replicarlo', 'How to replicate it')}</p><ul class="rpl">{rpl}</ul></div></div>
</article>'''
    s2 = f'''<section id="{l}-tendencias"><h2>{T('Tendencias de la semana', 'Trends of the week')}</h2>
  <p class="sub">{T('Lo que más funcionó en cuentas de fútbol (academias de clubes, fútbol juvenil de EE. UU., fútbol global), con un ejemplo real y cómo llevarlo a nuestras cuentas.', 'What worked best on soccer accounts (club academies, U.S. youth soccer, global soccer), with a real example and how to bring it to our accounts.')}</p>
  <div class="tends">{cards}</div></section>'''
    # 3. Hashtags
    hs = d.get('hashtags', {})
    filas_h = ''.join(
        f'<li class="hs"><div class="hs-a"><a class="hs-t" href="{E(tag_url(h["hashtag"]))}" target="_blank" rel="noopener">{E(h["hashtag"])}</a>'
        f'<span class="hs-d">{E(tx(h.get("desc", ""), l))}</span></div>'
        f'<div class="hs-b">{chispa(h.get("curva"))}<span class="hs-v">{E(vistas_cortas(h.get("vistas", ""), l))} {T("vistas", "views")}</span>'
        f'<a class="btn-s" href="{E(tag_url(h["hashtag"]))}" target="_blank" rel="noopener">{T("Ver videos", "See videos")} ↗</a></div></li>'
        for h in hs.get('filas', []))
    s3 = (f'''<section id="{l}-hashtags"><h2>{T('Hashtags en tendencia · TikTok', 'Trending hashtags · TikTok')}</h2>
  <p class="sub">{E(tx(hs.get("nota", ""), l))}</p><ul class="panel hss">{filas_h}</ul></section>''' if filas_h else '')
    # 4. Nuestras cuentas
    nu = d.get('nuestras', {})
    filas_n = ''.join(
        f'<div class="nu"><div class="nu-c">@{E(r["cuenta"].lstrip("@"))}</div><div class="nu-e nu-{E(r.get("nivel", "igual"))}">{E(tx(r.get("estado", ""), l))}</div></div>'
        for r in nu.get('filas', []))
    s4 = (f'''<section id="{l}-nuestras"><h2>{T('Cómo van nuestras cuentas', 'How our accounts are doing')}</h2>
  <p class="sub">{E(tx(nu.get("nota", ""), l))}</p><div class="panel nus">{filas_n}</div></section>''' if filas_n else '')
    # 5. Cómo se hace (plegado)
    met = ''.join(f'<li>{tx(m, l)}</li>' for m in d.get('metodo', []))
    arch = ''.join(f'<li><a href="{E(h)}?lang={l}">{E(t)}</a></li>' for t, h in otras)
    s5 = f'''<section id="{l}-metodo"><details class="panel det"><summary>{T('Cómo se hace este informe y ediciones anteriores', 'How this report is made and past editions')}</summary>
  <ul>{met}</ul>{('<p class="eyebrow">' + T('Ediciones anteriores', 'Past editions') + '</p><ul>' + arch + '</ul>') if arch else ''}</details></section>'''
    nav = [('resumen', T('Resumen', 'Summary')), ('tendencias', T('Tendencias', 'Trends'))]
    if s3: nav.append(('hashtags', 'Hashtags'))
    navh = ''.join(f'<a href="#{l}-{a}">{b}</a>' for a, b in nav)
    s4 = ''  # 15-11 (David): sin 'Cómo van nuestras cuentas'
    arch_pie = (f'<section class="arch"><span>' + T('Ediciones anteriores', 'Past editions') + ':</span> ' + ' · '.join(f'<a href="{E(h)}?lang={l}">{E(t)}</a>' for t, h in otras) + '</section>') if otras else ''
    return f'<nav><div class="in">{navh}</div></nav><main>{s1}{s2}{s3}{arch_pie}</main>'

def cabecera(d, l):
    es = l == 'es'
    act = d.get('actualizado')
    upd = ''
    if act:
        m = miami(act)
        upd = (f'<div class="upd"><span class="dot"></span><span>{"Actualizado" if es else "Updated"} <b>{E(fecha_hora(m, l))}</b></span>'
               f'<span class="sep">·</span><span>{"Se actualiza de forma automática el" if es else "Updates automatically on"} <b>{E(fecha_hora(proxima(m), l))}</b> <span class="mia">(Miami)</span></span></div>')
    ed = (f'Edición {d["numero"]} · semana del {tx(d["fecha_texto"], l)}' if es else f'Edition {d["numero"]} · week of {tx(d["fecha_texto"], l)}')
    return f'''<header><div class="in"><div class="top"><div>
<p class="eyebrow">{E(ed)}</p>
<h1>{'Tendencias en redes' if es else 'Social media trends'} <span>· {'Fútbol' if es else 'Soccer'}</span></h1>
<p class="lead">{'Qué está funcionando en redes alrededor del fútbol y qué podemos replicar en Athletum, Juve Miami y Juventus Camps.' if es else 'What is working on social media around soccer and what we can replicate at Athletum, Juve Miami and Juventus Camps.'}</p></div>
<div class="idioma" role="group" aria-label="Idioma / Language"><button type="button" data-set="es">ES</button><button type="button" data-set="en">EN</button></div></div>
{upd}</div></header>'''

CSS = '''
:root{--fondo:#101318;--panel:#191E26;--panel2:#222936;--tinta:#F5F7FA;--suave:#9AA4B2;--linea:#2A313D;--acento:#B7F34A;--sobre:#101318;--hover:#20262F}
*{box-sizing:border-box}html{color-scheme:dark}
body{margin:0;background:var(--fondo);color:var(--tinta);font:15px/1.55 Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:var(--acento)}
.in,main{max-width:1180px;margin:0 auto}
header{padding:28px 16px 18px;border-bottom:1px solid var(--linea)}
.top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
h1{margin:4px 0 0;font-size:clamp(26px,4vw,38px);font-weight:800;letter-spacing:-.01em;text-transform:uppercase;line-height:1.05}
h1 span{color:var(--acento)}
.lead{margin:8px 0 0;color:var(--suave);max-width:70ch}
.eyebrow{margin:0;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--suave)}
.upd{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin-top:14px;font-size:13px;color:var(--suave)}
.upd b{color:var(--tinta);font-weight:600}.upd .sep{opacity:.5}.mia{opacity:.8}
.dot{width:8px;height:8px;border-radius:50%;background:var(--acento);box-shadow:0 0 0 4px rgba(183,243,74,.15)}
.idioma{display:flex;border:1px solid var(--linea);border-radius:10px;overflow:hidden;flex:none}
.idioma button{background:none;border:0;color:var(--suave);font:700 12.5px Inter,system-ui;padding:8px 12px;cursor:pointer}
.idioma button[aria-pressed=true]{background:var(--acento);color:var(--sobre)}
nav{position:sticky;top:0;z-index:5;background:rgba(16,19,24,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--linea);overflow-x:auto;white-space:nowrap}
nav .in{padding:0 8px}nav a{display:inline-block;padding:12px 10px;color:var(--suave);text-decoration:none;font-size:13.5px;font-weight:600}nav a:hover{color:var(--tinta)}
main{padding:8px 16px 60px}section{margin-top:30px;scroll-margin-top:56px}
h2{font-size:20px;font-weight:800;text-transform:uppercase;letter-spacing:.02em;margin:0 0 4px}
h3{font-size:17px;font-weight:700;margin:0;line-height:1.25}
.sub{color:var(--suave);font-size:13.5px;margin:0 0 14px;max-width:80ch}
.panel{background:var(--panel);border:1px solid var(--linea);border-radius:14px;padding:18px}
.hero{padding:22px}.hero-t{font-size:clamp(17px,2.2vw,21px);font-weight:600;line-height:1.4;margin:8px 0 14px;max-width:70ch}
.tlist{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.tlist a{display:inline-flex;align-items:center;gap:8px;padding:7px 12px 7px 7px;border:1px solid var(--linea);border-radius:99px;color:var(--tinta);text-decoration:none;font-size:13.5px;font-weight:600;background:var(--panel2)}
.tlist a:hover{border-color:var(--acento)}
.tn{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--panel);border:1px solid var(--linea);font-size:12px;font-weight:800;flex:none}
.tn-g{width:32px;height:32px;font-size:15px;background:var(--acento);color:var(--sobre);border:0}
.reps{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:12px}
.rep{background:var(--panel);border:1px solid var(--linea);border-radius:14px;padding:16px}
.rep ul{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
.rep li{display:flex;gap:10px;align-items:flex-start;font-size:14px;line-height:1.45}
.rep-n{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:var(--panel2);border:1px solid var(--linea);font-size:11px;font-weight:800;flex:none;margin-top:1px}
.cta{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:99px;font-size:12px;font-weight:700;white-space:nowrap;border:1px solid var(--linea);color:var(--tinta);background:var(--panel2)}
.cta-athletum{border-color:#F2C230;color:#F2C230}.cta-juve-miami{border-color:#E8E8E8;color:#E8E8E8}.cta-juventus-camps{border-color:var(--acento);color:var(--acento)}
.tends{display:flex;flex-direction:column;gap:16px}
.tend-cab{display:flex;gap:12px;align-items:center}.orig{font-size:12px;color:var(--suave)}
.tend-q{margin:12px 0 6px;font-size:15px}
.dato{margin:0 0 14px;font-size:13.5px;color:var(--suave)}.dato b{color:var(--tinta);font-weight:600}
.tend-body{display:grid;gap:16px;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);align-items:start}
.ejs{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(240px,330px))}
.ej-c{font-size:12.5px;font-weight:700;color:var(--suave);margin-bottom:6px}.ej-s{font-size:12.5px;color:var(--suave);margin-top:6px;font-variant-numeric:tabular-nums}
.igp{min-height:140px;border-radius:12px;overflow:hidden;background:var(--panel2);display:flex;justify-content:center}
.igp-f{align-self:center;font-size:13px;color:var(--suave);padding:24px;text-decoration:none}
.igp .instagram-media{margin:0!important;min-width:0!important;width:100%!important;max-width:540px!important;border:0!important}
.cmo{background:var(--panel2);border:1px solid var(--linea);border-radius:12px;padding:16px}
.rpl{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:12px}
.rpl li{display:flex;flex-direction:column;gap:6px;align-items:flex-start;font-size:14px;line-height:1.45}
.hss{list-style:none;margin:0;padding:6px 18px}
.hs{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--linea);flex-wrap:wrap}.hs:last-child{border-bottom:0}
.hs-a{display:flex;flex-direction:column;min-width:0}.hs-t{font-weight:700;color:var(--tinta);text-decoration:none}.hs-t:hover{color:var(--acento)}
.hs-d{font-size:13px;color:var(--suave)}.hs-b{display:flex;align-items:center;gap:14px}
.chispa{color:var(--acento)}.hs-v{font-size:13px;color:var(--suave);min-width:80px;text-align:right}
.btn-s{display:inline-flex;align-items:center;height:30px;padding:0 10px;border-radius:9px;border:1px solid var(--linea);background:var(--panel2);color:var(--tinta);text-decoration:none;font-size:12.5px;font-weight:600;white-space:nowrap}
.btn-s:hover{border-color:var(--acento)}
.nus{display:grid;gap:0;padding:6px 18px}
.nu{display:flex;justify-content:space-between;gap:12px;padding:11px 0;border-bottom:1px solid var(--linea);flex-wrap:wrap}.nu:last-child{border-bottom:0}
.nu-c{font-weight:700}.nu-e{font-size:13.5px;color:var(--suave)}.nu-arriba{color:var(--acento)}
.arch{margin-top:36px;font-size:13px;color:var(--suave)}.arch a{color:var(--suave)}.det summary{cursor:pointer;font-weight:700}.det ul{color:var(--suave);font-size:13.5px}.det .eyebrow{margin-top:10px}
footer{max-width:1180px;margin:0 auto;padding:0 16px 40px;color:var(--suave);font-size:12.5px}
[data-l]{display:none}html[lang=es] [data-l=es],html[lang=en] [data-l=en]{display:block}
@media (max-width:820px){.tend-body{grid-template-columns:1fr}.top{flex-direction:column-reverse}.idioma{align-self:flex-end}}
'''

def pagina(d, otras, pref=''):
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Tendencias en redes · Fútbol</title>
<meta name="description" content="Qué está funcionando en redes alrededor del fútbol y qué replicar, cada semana.">
<meta property="og:title" content="Social media trends · Soccer"><meta property="og:description" content="Weekly: what is working on social media around soccer and what to replicate.">
<link rel="icon" type="image/svg+xml" href="{pref}favicon.svg"><meta name="theme-color" content="#101318">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<style>{CSS}</style>
</head>
<body>
<div data-l="es">{cabecera(d, 'es')}{cuerpo(d, 'es', otras)}</div>
<div data-l="en">{cabecera(d, 'en')}{cuerpo(d, 'en', otras)}</div>
<footer>Soccer Cage LLC · Marketing</footer>
<script>
(function(){{
  function elegir(){{
    try{{var q=new URLSearchParams(location.search).get('lang');if(q==='es'||q==='en')return q;}}catch(e){{}}
    try{{var g=localStorage.getItem('sc-lang');if(g==='es'||g==='en')return g;}}catch(e){{}}
    var n=(navigator.languages&&navigator.languages[0])||navigator.language||'es';return /^en/i.test(n)?'en':'es';
  }}
  function poner(l){{document.documentElement.lang=l;document.title=l==='en'?'Social media trends · Soccer':'Tendencias en redes · Fútbol';
    document.querySelectorAll('.idioma button').forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.set===l?'true':'false');}});}}
  var igListo=false,igCola=[];
  function igScript(cb){{if(window.instgrm){{cb();return;}}igCola.push(cb);if(igListo)return;igListo=true;var s=document.createElement('script');s.async=true;s.src='https://www.instagram.com/embed.js';
    s.onload=function(){{igCola.splice(0).forEach(function(f){{f();}});}};document.body.appendChild(s);}}
  var obs=('IntersectionObserver' in window)?new IntersectionObserver(function(es){{es.forEach(function(en){{if(en.isIntersecting){{obs.unobserve(en.target);cargar(en.target);}}}});}},{{rootMargin:'500px'}}):null;
  function cargar(el){{if(el.dataset.ok)return;el.dataset.ok='1';var u=el.dataset.ig.split('?')[0];
    el.innerHTML='<blockquote class="instagram-media" data-instgrm-permalink="'+u+'?utm_source=ig_embed" data-instgrm-version="14"></blockquote>';
    igScript(function(){{window.instgrm.Embeds.process();}});}}
  function vigilar(){{var l=document.documentElement.lang;document.querySelectorAll('[data-l="'+l+'"] .igp[data-ig]').forEach(function(el){{if(el.dataset.ok)return;if(obs)obs.observe(el);else cargar(el);}});}}
  poner(elegir());vigilar();
  document.querySelectorAll('.idioma button').forEach(function(b){{b.onclick=function(){{poner(b.dataset.set);vigilar();try{{localStorage.setItem('sc-lang',b.dataset.set);}}catch(e){{}}}};}});
}})();
</script>
</body></html>'''

FAV = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#101318"/><polyline points="10,44 24,30 34,38 52,18" fill="none" stroke="#B7F34A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><polyline points="40,18 52,18 52,30" fill="none" stroke="#B7F34A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'''

def main():
    todas = sorted(glob.glob(os.path.join(ED, '*.json')))
    ruta = sys.argv[1] if len(sys.argv) > 1 else todas[-1]
    d = json.load(io.open(ruta, encoding='utf-8'))
    os.makedirs(os.path.join(RAIZ, 'ediciones'), exist_ok=True)
    for r in todas:
        e = json.load(io.open(r, encoding='utf-8'))
        io.open(os.path.join(RAIZ, 'ediciones', e['fecha'] + '.html'), 'w', encoding='utf-8').write(pagina(e, [], '../'))
    otras = [(f'Edición {json.load(io.open(r, encoding="utf-8"))["numero"]} · {os.path.basename(r)[:-5]}', 'ediciones/' + os.path.basename(r)[:-5] + '.html')
             for r in reversed(todas) if os.path.abspath(r) != os.path.abspath(ruta)]
    io.open(os.path.join(RAIZ, 'index.html'), 'w', encoding='utf-8').write(pagina(d, otras))
    io.open(os.path.join(RAIZ, 'favicon.svg'), 'w', encoding='utf-8').write(FAV)
    # Resumen para la tarjeta de "Mercado y tendencias" del command center (la lee al abrir la página).
    ult = {'numero': d['numero'], 'fecha': d['fecha'], 'resumen': d.get('resumen', {}),
           'tendencias': [t['titulo'] for t in d.get('tendencias', [])],
           'replicar': {c: [{'es': r.get('es', ''), 'en': r.get('en', '')} for t in d.get('tendencias', []) for r in t.get('replicar', []) if r.get('cuenta') == c][:2] for c in CUENTAS},
           'destacadas': [dict({'titulo': t['titulo'], 'cuenta': t['ejemplos'][0]['cuenta'], 'enlace': t['ejemplos'][0]['enlace']},
                               **{k: t['ejemplos'][0][k] for k in ('likes', 'comentarios', 'vistas') if t['ejemplos'][0].get(k) is not None}) for t in d.get('tendencias', []) if t.get('ejemplos')],
           'auto': True,
           'url': 'https://almacenamiento982-blip.github.io/tendencias-redes-futbol/'}
    if d.get('actualizado'):
        m = miami(d['actualizado']); p = proxima(m)
        ult.update({'actualizado': d['actualizado'], 'act_txt': {l: fecha_hora(m, l) for l in ('es', 'en')}, 'prox_txt': {l: fecha_hora(p, l) for l in ('es', 'en')},
                    'prox_iso': p.strftime('%Y-%m-%dT%H:%M')})
    json.dump(ult, io.open(os.path.join(RAIZ, 'ultima.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ok', os.path.basename(ruta), '| ediciones:', len(todas))

if __name__ == '__main__':
    main()
