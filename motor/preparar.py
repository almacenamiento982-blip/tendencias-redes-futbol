# -*- coding: utf-8 -*-
"""Resume la lectura semanal del lector de Apps Script para escribir la edición.
   python motor/preparar.py <lectura.json> [dias=7]  -> imprime un resumen JSON (cifras exactas, sin inventar nada)
La lectura trae textos de publicaciones (pueden tener nombres de menores): NUNCA se guarda en el repo ni se copia a la página."""
import io, sys, json, statistics, datetime

def main():
    raw = json.load(io.open(sys.argv[1], encoding='utf-8'))
    dias = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    leido = datetime.datetime.fromisoformat(raw['leido'].replace('Z', '+00:00'))
    desde = (leido - datetime.timedelta(days=dias)).date().isoformat()
    out = {'leido': raw['leido'][:10], 'ventana_desde': desde, 'errores': raw.get('errores', []), 'tiktok_top_general': raw.get('tiktok'),
           'destacadas': [], 'por_formato': {}, 'cuentas': []}
    formatos = {}
    for grupo, cuentas in raw['grupos'].items():
        for c in cuentas:
            if c.get('error'):
                continue
            recientes = [p for p in c['posts'] if p['fecha'] >= desde]
            out['cuentas'].append({'grupo': grupo, 'cuenta': c['u'], 'seguidores': c['seguidores'], 'mediana_likes': c['mediana_likes'],
                                   'posts_semana': len(recientes), 'posts_leidos': len(c['posts']),
                                   'mejor_semana': max(recientes, key=lambda p: p['veces'] or 0, default=None) and {
                                       k: v for k, v in max(recientes, key=lambda p: p['veces'] or 0).items() if k != 'texto'}})
            for p in recientes:
                formatos.setdefault(p['tipo'], []).append(p['veces'] or 0)
                if (p['veces'] or 0) >= 2 and c['mediana_likes'] >= 20 and grupo != 'Nuestras cuentas':
                    out['destacadas'].append({'grupo': grupo, 'cuenta': c['u'], 'fecha': p['fecha'], 'tipo': p['tipo'], 'veces': p['veces'],
                                              'likes': p['likes'], 'comentarios': p['comentarios'], 'vistas': p.get('vistas'), 'enlace': p['enlace'], 'texto_para_entender': p['texto'][:280]})
    out['destacadas'].sort(key=lambda x: -x['veces'])
    out['por_formato'] = {t: {'publicaciones': len(v), 'mediana_veces': round(statistics.median(v), 2)} for t, v in formatos.items()}
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
