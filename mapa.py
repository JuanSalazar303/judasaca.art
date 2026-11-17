# -*- coding: utf-8 -*-
"""Mapa de puntos del mundo, dibujado al construir el sitio.

No es un mapa de verdad: son poligonos muy gruesos de cada continente que se
rasterizan a una reja de puntos. A esta resolucion se reconoce igual y pesa
dos kilobytes en vez de medio mega.
"""
CONTINENTES = [
 # Norteamerica
 [(-168,66),(-140,70),(-120,72),(-95,74),(-80,73),(-60,68),(-55,52),(-66,45),
  (-70,42),(-76,36),(-81,25),(-90,29),(-97,26),(-106,23),(-114,30),(-124,40),
  (-124,48),(-135,58),(-150,60),(-168,66)],
 # Centroamerica
 [(-92,18),(-84,16),(-78,9),(-77,7),(-83,8),(-88,13),(-92,18)],
 # Suramerica
 [(-81,8),(-72,11),(-62,10),(-52,5),(-45,-2),(-35,-6),(-38,-13),(-48,-25),
  (-53,-34),(-58,-39),(-62,-41),(-65,-45),(-71,-53),(-75,-50),(-73,-42),
  (-71,-30),(-70,-18),(-76,-6),(-80,0),(-78,5),(-81,8)],
 # Europa
 [(-10,36),(-2,36),(5,43),(12,38),(18,40),(24,36),(28,41),(30,45),(40,47),
  (40,56),(30,60),(28,66),(22,70),(12,65),(5,60),(-2,56),(-6,54),(-10,50),(-10,36)],
 # Africa
 [(-17,15),(-10,25),(0,32),(10,34),(20,32),(32,31),(35,24),(39,15),(43,11),
  (51,11),(43,0),(40,-10),(38,-18),(33,-26),(26,-34),(18,-34),(12,-18),(9,-2),
  (5,5),(-5,5),(-13,9),(-17,15)],
 # Asia
 [(28,41),(45,40),(50,45),(60,45),(70,42),(78,34),(88,28),(95,27),(98,16),
  (104,10),(109,11),(107,20),(112,22),(121,31),(122,40),(128,43),(135,45),
  (143,45),(150,59),(160,61),(170,66),(178,68),(160,72),(130,73),(100,77),
  (70,73),(50,68),(40,66),(40,47),(28,41)],
 # India
 [(68,24),(72,21),(73,16),(77,8),(80,13),(84,19),(88,22),(88,26),(80,28),(72,28),(68,24)],
 # Japon
 [(130,32),(136,35),(140,37),(142,42),(145,44),(141,45),(138,37),(133,34),(130,32)],
 # Indonesia / sudeste
 [(95,5),(105,1),(115,-2),(125,-3),(135,-3),(140,-8),(130,-8),(118,-9),(105,-7),(95,5)],
 # Australia
 [(114,-22),(122,-18),(130,-12),(137,-12),(143,-12),(146,-19),(151,-25),
  (153,-28),(150,-37),(145,-38),(137,-35),(129,-32),(118,-34),(114,-22)],
 # Nueva Zelanda
 [(172,-41),(174,-37),(178,-38),(176,-41),(172,-46),(167,-46),(172,-41)],
 # Islas britanicas
 [(-6,50),(-2,53),(-1,58),(-5,58),(-8,55),(-6,50)],
]

CIUDADES = {
 'New York City': (40.71, -74.01), 'Miami': (25.76, -80.19),
 'Los Angeles': (34.05, -118.24), 'Bogotá': (4.71, -74.07),
 'Tokyo': (35.68, 139.65), 'Lisbon': (38.72, -9.14),
 'Algarve': (37.02, -7.93), 'Barcelona': (41.39, 2.17),
 'Mexico City': (19.43, -99.13), 'Costa Rica': (9.93, -84.08),
 'Lima': (-12.05, -77.04),
}

# Para las entradas que dicen solo el pais, sin ciudad.
CENTROS = {'Portugal': (39.5, -8.0), 'Costa Rica': (9.93, -84.08),
           'Colombia': (4.71, -74.07), 'USA': (39.0, -98.0),
           'Spain': (40.4, -3.7), 'Japan': (36.2, 138.3),
           'Mexico': (23.6, -102.5), 'Peru': (-9.2, -75.0)}

LAT_MAX, LAT_MIN = 74, -52
COLS, FILAS = 78, 34

def _dentro(x, y, poli):
    n = len(poli); dentro = False; j = n - 1
    for i in range(n):
        xi, yi = poli[i]; xj, yj = poli[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro

def proyecta(lat, lon, w=1000, h=430):
    x = (lon + 180) / 360.0 * w
    y = (LAT_MAX - lat) / float(LAT_MAX - LAT_MIN) * h
    return x, y

def mapa_svg(w=1000, h=430):
    puntos = []
    for c in range(COLS):
        for f in range(FILAS):
            lon = -180 + (c + .5) / COLS * 360
            lat = LAT_MAX - (f + .5) / FILAS * (LAT_MAX - LAT_MIN)
            if any(_dentro(lon, lat, p) for p in CONTINENTES):
                x, y = proyecta(lat, lon, w, h)
                puntos.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6"/>')
    return ''.join(puntos)

def caja_de(nombres, w=1000, h=430):
    """Rectangulo que encierra esas ciudades, en coordenadas del dibujo."""
    pts = [proyecta(*CIUDADES[n], w=w, h=h) for n in nombres if n in CIUDADES]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def pines_svg(ciudades, w=1000, h=430):
    """ciudades: lista de (nombre, pais, anios).

    Cada pin lleva los anios en que hubo exposicion ahi, para que la linea de
    tiempo pueda encenderlo sola al pasar por ese anio.
    """
    out = []
    for nombre, pais, anios in ciudades:
        if nombre not in CIUDADES: continue
        lat, lon = CIUDADES[nombre]
        x, y = proyecta(lat, lon, w, h)
        out.append(
          f'<g class="pin" data-pais="{pais}" data-anios="{" ".join(sorted(anios))}" '
          f'transform="translate({x:.1f},{y:.1f})">'
          f'<circle class="halo" r="13"/><circle class="pulso" r="5"/>'
          f'<circle class="punto" r="5"/>'
          f'<text y="-17">{nombre}</text></g>')
    return ''.join(out)


def tile_ciudad(nombre, ancho=110.0, alto=147.0, fino=2):
    """Mapa de puntos acercado a un lugar, para la tarjeta sin foto.

    Antes ahi iba texto sobre un fondo vacio y se veia como un hueco. Esto es
    informacion de verdad, cambia en cada lugar y usa el mismo dibujo del mapa
    grande, asi que la pagina se siente de una sola pieza.

    Los puntos se agrupan en tres bandas de opacidad y las coordenadas van
    redondeadas: con un atributo de opacidad por punto, once mosaicos pesaban
    mas que todo el resto de la pagina junta.
    """
    pos = CIUDADES.get(nombre) or CENTROS.get(nombre)
    if not pos:
        return None
    cx, cy = proyecta(*pos)
    x0, y0 = cx - ancho / 2, cy - alto / 2
    r = max(ancho, alto) / 2.0

    cols, filas = COLS * fino, FILAS * fino
    bandas = {0: [], 1: [], 2: []}
    for c in range(cols):
        lon = -180 + (c + .5) / cols * 360
        for f in range(filas):
            lat = LAT_MAX - (f + .5) / filas * (LAT_MAX - LAT_MIN)
            x, y = proyecta(lat, lon)
            if not (x0 - 4 <= x <= x0 + ancho + 4 and y0 - 4 <= y <= y0 + alto + 4):
                continue
            if not any(_dentro(lon, lat, p) for p in CONTINENTES):
                continue
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** .5 / r
            bandas[0 if d < .35 else 1 if d < .7 else 2].append(
                f'<circle cx="{x:.0f}" cy="{y:.0f}"/>')

    tierra = ''.join(
        f'<g opacity="{op}">{"".join(bandas[k])}</g>'
        for k, op in ((0, '1'), (1, '.6'), (2, '.3')) if bandas[k])
    anillos = ''.join(
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{k}" fill="none" '
        f'stroke="var(--pin,#C9421F)" stroke-width=".8" opacity="{0.3 - k * 0.009:.2f}"/>'
        for k in (9, 15, 22))
    return (f'{x0:.0f} {y0:.0f} {ancho:.0f} {alto:.0f}',
            f'<g fill="var(--tierra,#5E5B57)" r="1.6">{tierra}</g>'
            f'<g>{anillos}<circle cx="{cx:.0f}" cy="{cy:.0f}" r="2.8" '
            f'fill="var(--pin,#C9421F)"/></g>')


def tile_digital(ancho=110.0, alto=147.0):
    """Para la muestra que no ocurrio en ningun lugar: una reja pareja.

    No lleva costas porque no hubo sitio. La reja uniforme dice justamente eso.
    """
    puntos = []
    for c in range(14):
        for f in range(19):
            puntos.append(f'<circle cx="{c * 8 + 4}" cy="{f * 8 + 4}"/>')
    cx, cy = 56, 76
    anillos = ''.join(
        f'<circle cx="{cx}" cy="{cy}" r="{k}" fill="none" stroke="var(--pin,#C9421F)" '
        f'stroke-width=".8" opacity="{0.3 - k * 0.009:.2f}"/>' for k in (9, 15, 22))
    return (f'0 0 {ancho:.0f} {alto:.0f}',
            f'<g fill="var(--tierra,#5E5B57)" r="1.6" opacity=".5">{"".join(puntos)}</g>'
            f'<g>{anillos}<circle cx="{cx}" cy="{cy}" r="2.8" fill="var(--pin,#C9421F)"/></g>')
