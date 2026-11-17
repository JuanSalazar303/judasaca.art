#!/usr/bin/env python3
"""
Generador del sitio judasaca.art

Todo el contenido vive aqui arriba, en OBRAS, EXPOS y PRENSA. Se corre
`python3 build.py` y se reescriben los seis HTML. La ventaja de tenerlo asi
es que la barra, el pie y las etiquetas de Google quedan identicas en todas
las paginas: no hay forma de que una quede desactualizada.

Para marcar una obra como vendida: pon vendida=True. Toda obra que no este
vendida lleva boton de compra; el precio lo decide el Worker, no esta pagina.
"""
import os, re, html, hashlib, json
import mapa

RUTA = os.path.dirname(os.path.abspath(__file__))
SITIO = 'https://judasaca.art'
CORREO = 'contact@judasaca.art'
IG = 'https://www.instagram.com/judasaca'
TIKTOK = 'https://www.tiktok.com/@judasaca'
IG_ESTUDIO = 'https://www.instagram.com/303artstudio'

# ── pagos con Bold ───────────────────────────────────────────────────────
# La llave de IDENTIDAD es publica y va en el HTML: solo dice a que comercio
# pertenece el cobro. La llave SECRETA no esta aqui ni en este repositorio,
# vive como secreto del Worker de Cloudflare.
LLAVE_IDENTIDAD = '2heS56eZeRZj1n1B8NDPF9_LA2aDpNbyNBJOoG65qWI'
FIRMADOR = 'https://judasaca-bold.judasaca-art.workers.dev'

# Tope de tarjeta de Bold: 5.000.000 COP. A la TRM que usa el dossier (3.361,62)
# son unos 1.487 dolares.
#
# YA NO ESCONDE NINGUN BOTON. Por decision de Juan, toda obra que no este
# vendida se puede comprar de una.
#
# Comprobado el 25/08/2026: pasarse del tope NO da el error BTN-002. Bold
# muestra una pantalla distinta que dice "monto maximo excedido". Asi que el
# tope no era la causa de la falla que vimos, y este numero queda solo como
# dato: subirlo se pide a soporte.online@bold.co.
TOPE_TARJETA_USD = 1487

# ── formulario de contacto ───────────────────────────────────────────────
# Un sitio estatico no puede mandar correo por si solo: no hay servidor detras.
# Web3Forms recibe el envio y lo reenvia a CORREO. Se saca la llave en
# web3forms.com poniendo contact@judasaca.art, llega por correo, y se pega aqui.
# Mientras diga PEGA-AQUI, el formulario no envia nada.
LLAVE_FORM = '511aafa4-63bd-453c-a671-8825c5104c7a'
REEL = 'https://www.instagram.com/reel/DXqQrk9l-U-/'

# ── las obras ────────────────────────────────────────────────────────────
# El campo 'buy' quedo de la epoca de Stripe y ya no se usa: hoy el cobro lo
# arma el Worker a partir del slug. vendida=True es lo unico que apaga la venta.
OBRAS = [
 dict(slug='artwork-incoming',     titulo='Artwork Incoming',
      tec='Next release',                     med='Coming soon', usd=0, buy='', vendida=False,
      proxima=True,
      nota='50% of this sale will be donated to St Jude Children’s Research Hospital'),
 dict(slug='snoopin-aint-easy',    titulo='Snoopin Ain’t Easy',
      tec='Acrylics and spray on canvas',     med='100 × 100 cm', usd=2000, buy='', vendida=False),
 dict(slug='rendered-reality',     titulo='Rendered Reality',
      tec='Mixed media on canvas',            med='75 × 100 cm', usd=2200, buy='', vendida=True,
      nota='Exhibited at Jutta Gallery, New York City · Space Between Worlds'),
 dict(slug='oil-city-woodstock',   titulo='Oil City Woodstock',
      tec='Acrylics and oil stick on canvas', med='100 × 100 cm', usd=1950, buy='', vendida=False),
 dict(slug='sunday-snoops',        titulo='Sunday, Snoops',
      tec='Acrylics and spray on canvas',     med='100 × 100 cm', usd=1950, buy='', vendida=False),
 dict(slug='pop-art-rat',          titulo='Pop Art Rat',
      tec='Acrylics and oil stick on canvas', med='100 × 100 cm', usd=1950, buy='', vendida=True),
 dict(slug='mango-og',             titulo='Mango OG',
      tec='Acrylics and oil stick on canvas', med='95 × 95 cm', usd=1950, buy='', vendida=False),
 dict(slug='original-pastel-disney', titulo='Original Pastel Disney',
      tec='Acrylics and spray on canvas',     med='100 × 100 cm', usd=1950, buy='', vendida=False),
 dict(slug='nothing-stays-the-same', titulo='Nothing Stays the Same',
      tec='Oil on canvas',                    med='100 × 120 cm', usd=1950, buy='', vendida=True),
 # recorte=True: la obra es redonda y su foto no es cuadrada, asi que dentro del
 # marco cuadrado quedaba flotando con franjas arriba y abajo. Con recorte llena
 # el marco y se le quita lo que sobra por arriba y por abajo.
 dict(slug='blue-thoughts-rat',    titulo='Blue Thoughts Rat',
      tec='Acrylics and spray on canvas',     med='80 cm diameter', usd=1235, buy='',
      vendida=False, recorte=True),
 dict(slug='smiling-ratsquiat-blue-crown', titulo='Smiling Ratsquiat, Blue Crown',
      tec='Acrylics and spray on canvas',     med='50 × 50 cm', usd=975, buy='', vendida=False),
 dict(slug='oil-woodstock',        titulo='Oil Woodstock',
      tec='Acrylics and oil on canvas',       med='50 × 50 cm', usd=975, buy='', vendida=False),
 dict(slug='here-love',            titulo='Here, Love',
      tec='Acrylics and spray on canvas',     med='50 × 50 cm', usd=975, buy='', vendida=True),
 dict(slug='cloud-city-snoops',    titulo='Cloud City Snoops',
      tec='Oil on canvas',                    med='50 × 50 cm', usd=1000, buy='', vendida=False),
 dict(slug='new-york-street-snoops', titulo='New York Street Snoops',
      tec='Acrylics and spray on canvas',     med='50 × 50 cm', usd=975, buy='', vendida=False),
 dict(slug='city-rounds-icon',     titulo='City Rounds Icon',
      tec='Oil on canvas',                    med='50 × 50 cm', usd=1000, buy='', vendida=False),
 # ── entradas de agosto de 2026 ──
 # OJO JUAN: las tecnicas de estas tres las puse yo mirando las fotos.
 # Si alguna esta mal, se corrige aqui y solo aqui.
 dict(slug='city-famous-rat',      titulo='City Famous Rat',
      tec='Acrylics and spray on canvas',     med='175 × 80 cm', usd=2600, buy='', vendida=False,
      ancha=True),
 dict(slug='broken-icon',          titulo='Broken Icon',
      tec='Acrylics and oil stick on canvas', med='100 × 100 cm', usd=1950, buy='', vendida=False),
 dict(slug='smiling-ratsquiat-yellow-crown', titulo='Smiling Ratsquiat, Yellow Crown',
      tec='Acrylics and spray on canvas',     med='50 × 50 cm', usd=975, buy='', vendida=False),
]

# ── la tienda ────────────────────────────────────────────────────────────
# Ocho originales unicos de 45 × 40 y las medias. Van por el mismo Worker que
# el arte: mismo boton, mismo carrito, misma marca de vendida. La unica
# diferencia es en que pagina salen.
#
# Las ocho son crayon de oleo sobre papel, confirmado por Juan.
TIENDA = [
 dict(slug='woodstocks-on-fire',   titulo='Woodstock’s on Fire',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 dict(slug='out-in-the-beach-rat', titulo='Out in the Beach Rat',
      tec='Acrylic markers on USPS Label 228 sticker', med='Framed', usd=180, buy='', vendida=False),
 dict(slug='out-in-the-city-woodstock', titulo='Out in the City, Woodstock',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 dict(slug='colour-pop-snoops',    titulo='Colour Pop Snoops',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 dict(slug='icon-kiss',            titulo='Icon Kiss',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 dict(slug='palometa-tribute',     titulo='Palometa Tribute',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 dict(slug='city-of-rats',         titulo='City of Rats',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
 # OJO JUAN: de esta no te acordabas el material. Lo puse generico. Se corrige aqui.
 dict(slug='abstract-reality-icon', titulo='Abstract Reality Icon',
      tec='Mixed media on canvas', med='35 × 25 cm', usd=600, buy='', vendida=False),
 dict(slug='everything-will-be-ok-jules', titulo='Everything Will Be OK, Jules',
      tec='Oil pastel on high quality cotton paper', med='Framed 45 × 40 cm', usd=250, buy='', vendida=False),
]


# Las medias se venden como un solo producto: las dos parejas juntas. Cada
# pareja sale de un cuadro distinto, y esos dos cuadros se muestran al lado
# en la pagina. Por eso van aparte y no dentro de TIENDA.
MEDIAS = dict(slug='judasaca-socks', titulo='Broken Icon × Bitcoin Rat Socks',
              tec='Printed from two original paintings',
              med='Two pairs', usd=30, buy='', vendida=False)

# ── exposiciones ─────────────────────────────────────────────────────────
EXPOS = [
 ('2027', [dict(nombre='Los Angeles Art Show · Verse Gallery', lugar='Los Angeles, USA',
                premio='', foto='', estado='upcoming', tipo='grupo')]),
 ('2026', [dict(nombre='Miami Art Week', lugar='Miami, USA',
                premio='', foto='', estado='upcoming', tipo='grupo'),
           dict(nombre='Canal Street Show · Art Battle', lugar='New York City, USA',
                premio='Winner', foto='cv-canal-street-2026', estado='', tipo='grupo'),
           dict(nombre='FREEMAN’S Alley', lugar='New York City, USA',
                premio='', foto='cv-freemans-alley-2026', estado='', tipo='grupo'),
           dict(nombre='JUTTA Gallery', lugar='New York City, USA',
                premio='', foto='cv-jutta-2026', estado='', tipo='grupo'),
           dict(nombre='OKUPA Art Expo', lugar='Museo Casa Lleras, Universidad Jorge Tadeo Lozano · Bogotá',
                premio='', foto='cv-okupa-2026', estado='', tipo='duo'),
           dict(nombre='OKUPA Art Expo · Opening', lugar='Bogotá, Colombia',
                premio='', foto='cv-okupa-flyer', estado='', tipo='duo'),
           dict(nombre='NFT NYC · Speaker', lugar='New York City, USA',
                premio='', foto='', estado='', tipo='charla')]),
 ('2025', [dict(nombre='Sacred Origins · JUTTA Gallery', lugar='New York City, USA',
                premio='', foto='cv-sacred-origins-2025', estado='', tipo='grupo'),
           dict(nombre='BRANDALISM · Solo exhibition', lugar='Bogotá, Colombia',
                premio='', foto='cv-brandalism-2025', estado='', tipo='solo'),
           dict(nombre='NFT NYC · Speaker', lugar='New York City, USA',
                premio='', foto='', estado='', tipo='charla')]),
 ('2024', [dict(nombre='NFT NYC · Featured Artist', lugar='New York City, USA',
                premio='', foto='cv-nftnyc-2024', estado='', tipo='grupo'),
           dict(nombre='NFT NYC · Speaker', lugar='New York City, USA',
                premio='', foto='cv-nftnyc-2024-b', estado='', tipo='charla'),
           dict(nombre='Times Square Digital Takeover', lugar='New York City, USA',
                premio='', foto='cv-nyc-takeover-2024', estado='', tipo='grupo'),
           dict(nombre='One Love Art DAO · Wynwood', lugar='Miami, USA',
                premio='', foto='cv-wynwood-2024', estado='', tipo='grupo'),
           dict(nombre='Miami Art Week · Public murals and exhibitions', lugar='Miami, USA',
                premio='', foto='cv-nftnyc-2024-c', estado='', tipo='grupo'),
           dict(nombre='Oculus Center Fall Exhibition', lugar='New York City, USA',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Street Art Expo', lugar='OBJKT digital exhibition',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Ordinals Meet Up', lugar='Mexico City, Mexico',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='SoyArte PLAY', lugar='Bogotá, Colombia',
                premio='', foto='', estado='', tipo='grupo')]),
 ('2023', [dict(nombre='5th Colombian Art Salon', lugar='Tokyo, Japan',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='UNGA78 Latine Art Exhibition', lugar='New York City, USA',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='NFT NYC', lugar='New York City, USA',
                premio='', foto='cv-nftnyc-2023', estado='', tipo='grupo'),
           dict(nombre='GoFest · Cámara de Comercio de Bogotá', lugar='Ágora · Bogotá, Colombia',
                premio='', foto='cv-gofest-2023', estado='', tipo='grupo'),
           dict(nombre='GoFest · ChromaVerse panel', lugar='Bogotá, Colombia',
                premio='', foto='cv-gofest-2023-flyer', estado='', tipo='grupo'),
           dict(nombre='BlockDown Festival', lugar='Algarve, Portugal',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Blockchain Jungle · ChromaVerse Jungle', lugar='Costa Rica',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='One Love Art Festival · Miami Art Week', lugar='Miami, USA',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Chromaflora · Hybrid Art Exhibition', lugar='Lisbon, Portugal',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='BlockchainCon', lugar='Lima, Peru',
                premio='Dynamic Artwork Award', foto='', estado='', tipo='grupo'),
           dict(nombre='Artsies Collective Digital Exhibition', lugar='Barcelona, Spain',
                premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Artsies Collective Digital Exhibition', lugar='Portugal',
                premio='', foto='', estado='', tipo='grupo')]),
 ('2022', [dict(nombre='Bogotá NFT Art Expo', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='LG Electronics × Zientte NFT Exhibition', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Blockchain Summit Latam', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Arte y Tecnología', lugar='Centro Comercial Avenida Chile · Bogotá', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='ARTRADE × KARE', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo')]),
 ('2021', [dict(nombre='We Art Colombia', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='We Art Colombia', lugar='Miami, USA', premio='', foto='cv-miami-2021', estado='', tipo='grupo'),
           dict(nombre='Art PRBLMS 2', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo'),
           dict(nombre='Open San Felipe', lugar='Bogotá, Colombia', premio='', foto='', estado='', tipo='grupo')]),
]

PRENSA = [
 ('El Espectador', 'Judasaca presenta ‘Brandalism’, arte que cuestiona el poder de las marcas',
  'https://www.elespectador.com/especiales/judasaca-presenta-brandalism-arte-que-cuestiona-el-poder-de-las-marcas/'),
 ('ColombiaOne', 'Judasaca: Colombian Artist Reimagines Pop Culture with Tech, Color, and NFTs',
  'https://colombiaone.com/2025/10/18/judasaca-colombian-artist-nfts/'),
 ('Universidad Jorge Tadeo Lozano', 'Street art y realidad aumentada se toman el Museo Biblioteca Carlos Lleras Restrepo',
  'https://www.utadeo.edu.co/es/eventos/street-art-y-realidad-aumentada-se-toman-el-museo-biblioteca-carlos-lleras-restrepo-con-la'),
 ('Plaza Capital', 'El arte digital, una apuesta por la innovación',
  'https://plazacapital.co/innovacion/7273-el-arte-digital-una-apuesta-por-la-innovacion'),
]

PAISES = {'Colombia':'Colombia', 'USA':'United States', 'Japan':'Japan',
          'Portugal':'Portugal', 'Costa Rica':'Costa Rica', 'Peru':'Peru',
          'Spain':'Spain', 'Mexico':'Mexico', 'Digital':'Online'}

def cuenta():
    n = sum(len(i) for _, i in EXPOS)
    paises = set()
    for _, items in EXPOS:
        for it in items:
            lugar = it['lugar']
            for clave in PAISES:
                if clave in lugar:
                    paises.add(clave)
    # Bogota y Miami aparecen sin pais en algunas lineas
    if any('Bogotá' in i['lugar'] for _, its in EXPOS for i in its): paises.add('Colombia')
    if any('Miami' in i['lugar'] for _, its in EXPOS for i in its): paises.add('USA')
    anios = [int(a) for a, _ in EXPOS]
    return n, len(paises), min(anios)

N_EXPOS, N_PAISES, ANIO_0 = cuenta()
# El titular dice exposiciones, asi que las charlas no cuentan ahi. Inflar ese
# numero es justo lo que hace que un curador desconfie de la lista entera.
N_MUESTRAS = sum(1 for _, its in EXPOS for i in its if i.get('tipo') != 'charla')
ANIO_FIN = max(int(a) for a, _ in EXPOS)

# Lo que un curador busca en los primeros diez segundos: si hay individual, en
# que galerias ha estado y si tiene premios. Estaba todo enterrado entre las
# cuarenta y una lineas, que es como no tenerlo.
_destacados = []
for _a, _its in EXPOS:
    for _i in _its:
        if _i.get('tipo') == 'solo':
            _destacados.append(('Solo exhibition', _i['nombre'].split(' · ')[0],
                                f"{_i['lugar']} · {_a}"))
_gal = [(a, i) for a, its in EXPOS for i in its if 'Gallery' in i['nombre']]
if _gal:
    _destacados.append(('Galleries', ' · '.join(sorted({
        i['nombre'].split(' · ')[-1] if 'Gallery' in i['nombre'].split(' · ')[-1]
        else i['nombre'] for _, i in _gal})), ''))
_prem = [(a, i) for a, its in EXPOS for i in its if i.get('premio')]
if _prem:
    _destacados.append(('Awards', ' · '.join(f"{i['premio']}, {i['nombre'].split(' · ')[0]}"
                                             for _, i in _prem), ''))
DESTACADOS = '\n        '.join(
  f'<div class="hito"><span class="eti">{html.escape(e)}</span>'
  f'<b>{html.escape(t)}</b>{f"<span>{html.escape(d)}</span>" if d else ""}</div>'
  for e, t, d in _destacados)

PAGINAS = [('index.html', 'Home'), ('about.html', 'About'), ('art.html', 'Art'),
           ('shop.html', 'Shop'), ('cv.html', 'CV'), ('contact.html', 'Contact')]


def nav(activa):
    ls = []
    for arch, nom in PAGINAS:
        if nom == 'Home':
            continue
        on = ' class="on"' if arch == activa else ''
        ls.append(f'<a href="{arch}"{on}>{nom}</a>')
    return '\n      '.join(ls)


# ── lo que Google lee y el visitante no ve ───────────────────────────────
# Una persona entra al sitio y entiende en dos segundos que Judasaca es un
# pintor de Bogota. Un buscador no: para el son palabras sueltas en una
# pagina. Esto se lo dice en su idioma, que es un JSON con tipos de
# schema.org, y de paso enlaza el nombre artistico con el nombre real y con
# la prensa que ya lo cubrio. Es lo que hace que buscar "judasaca" traiga
# esta pagina y no solo los perfiles de redes.
#
# Regla de oro: aqui no se escribe nada que no este escrito tambien en la
# pagina. Marcar un precio que el visitante no ve es motivo de penalizacion,
# y con razon.

REDES = ['https://www.instagram.com/judasaca',
         'https://www.tiktok.com/@judasaca',
         'https://x.com/judasaca_art']

# ── la insignia de "fuente preferida" de Google ──────────────────────────
# Existe y son dos lineas, pero hoy no sirve de nada aqui y por eso no esta
# puesta. Google solo la deja funcionar si el dominio ya aparece en su
# herramienta de fuentes, y ahi solo entran sitios que el buscador ya tiene
# indexados y que publican cosa nueva a menudo. judasaca.art todavia no esta
# ni indexado, asi que el boton llevaria a una pagina que dice "no hay nada".
#
# Se comprueba en diez segundos abriendo esto en el navegador:
#     https://www.google.com/preferences/source?q=judasaca.art
# Si el sitio sale ahi, se descomenta esto y ya esta:
#
#     <script async src="https://news.google.com/swg/js/v1/publisher.js"></script>
#     <div google-add-preferred-source-btn data-theme="dark"></div>
#
# Mientras tanto es un script de terceros en todas las paginas a cambio de
# nada, y con la pagina de privacidad que tiene el sitio, eso no sale a
# cuenta. Primero que Google sepa que la pagina existe.


def medidas(med):
    """De '100 × 120 cm' saca alto y ancho por separado.

    Devuelve lista vacia si no encuentra dos numeros, que es el caso de las
    redondas ('80 cm diameter') y las de la tienda ('Framed'). Preferimos no
    decir nada antes que decir algo aproximado.
    """
    nums = re.findall(r'(\d+(?:[.,]\d+)?)\s*[×x]\s*(\d+(?:[.,]\d+)?)', med)
    if not nums:
        return {}
    a, b = nums[0]
    return {'width':  {'@type': 'QuantitativeValue', 'value': float(b), 'unitCode': 'CMT'},
            'height': {'@type': 'QuantitativeValue', 'value': float(a), 'unitCode': 'CMT'}}


def artista():
    """La ficha de Juan. Es el nodo al que apuntan todos los demas."""
    return {
        '@type': 'Person',
        '@id': SITIO + '/#judasaca',
        'name': 'Juan Salazar',
        'alternateName': 'JUDASACA',
        'url': SITIO + '/',
        'image': SITIO + '/about_photo.webp',
        'jobTitle': 'Visual artist',
        'nationality': {'@type': 'Country', 'name': 'Colombia'},
        'homeLocation': {'@type': 'Place',
                         'address': {'@type': 'PostalAddress',
                                     'addressLocality': 'Bogotá',
                                     'addressCountry': 'CO'}},
        'knowsAbout': ['Painting', 'Street art', 'Augmented reality',
                       'Digital art', 'Pop art'],
        # sameAs es "esta persona, en otro sitio". Solo perfiles suyos: si se
        # meten aqui los articulos de prensa se le esta diciendo a Google que
        # El Espectador es Juan, que no es el caso.
        'sameAs': REDES,
        # subjectOf si es lo correcto para la prensa: obras que hablan de el.
        'subjectOf': [{'@type': 'Article', 'headline': t, 'url': u,
                       'publisher': {'@type': 'Organization', 'name': medio}}
                      for medio, t, u in PRENSA],
    }


def obra_json(o, pagina):
    """Una obra, como producto y como pieza de arte a la vez.

    Los dos tipos son ciertos y schema.org deja combinarlos: es un cuadro y
    ademas esta en venta. El precio solo se declara si de verdad se puede
    comprar; en las vendidas la pagina no muestra precio, asi que aqui
    tampoco va.
    """
    d = {
        '@type': ['VisualArtwork', 'Product'],
        '@id': f'{SITIO}/{pagina}#{o["slug"]}',
        'name': o['titulo'],
        'image': f'{SITIO}/img/{o["slug"]}.webp',
        'url': f'{SITIO}/{pagina}',
        'artform': 'Painting',
        'artMedium': o['tec'],
        'description': f'{o["tec"]}. {o["med"]}.',
        'creator': {'@id': SITIO + '/#judasaca'},
        'artist': {'@id': SITIO + '/#judasaca'},
    }
    d.update(medidas(o['med']))
    if o['vendida']:
        d['offers'] = {'@type': 'Offer', 'url': f'{SITIO}/{pagina}',
                       'availability': 'https://schema.org/SoldOut'}
    else:
        d['offers'] = {'@type': 'Offer', 'url': f'{SITIO}/{pagina}',
                       'price': o['usd'], 'priceCurrency': 'USD',
                       'availability': 'https://schema.org/InStock',
                       'itemCondition': 'https://schema.org/NewCondition',
                       'seller': {'@id': SITIO + '/#judasaca'}}
    return d


def lista(obras, pagina):
    return {'@type': 'ItemList',
            'itemListElement': [{'@type': 'ListItem', 'position': i,
                                 'item': obra_json(o, pagina)}
                                for i, o in enumerate(obras, 1)]}


def datos(activa, canon):
    """El bloque que se mete en cada pagina, distinto segun cual sea."""
    nodos = [{'@type': 'WebSite', '@id': SITIO + '/#sitio',
              'url': SITIO + '/', 'name': 'JUDASACA', 'inLanguage': 'en',
              'publisher': {'@id': SITIO + '/#judasaca'}}]

    if activa == 'index.html':
        nodos.append(artista())
        nodos.append({'@type': 'WebPage', '@id': canon + '#pagina',
                      'url': canon, 'isPartOf': {'@id': SITIO + '/#sitio'},
                      'about': {'@id': SITIO + '/#judasaca'}})

    elif activa in ('about.html', 'cv.html'):
        nodos.append(artista())
        nodos.append({'@type': 'ProfilePage', '@id': canon + '#pagina',
                      'url': canon, 'isPartOf': {'@id': SITIO + '/#sitio'},
                      'mainEntity': {'@id': SITIO + '/#judasaca'}})

    elif activa == 'art.html':
        nodos.append({'@type': 'CollectionPage', '@id': canon + '#pagina',
                      'url': canon, 'name': 'Original works',
                      'isPartOf': {'@id': SITIO + '/#sitio'},
                      'mainEntity': lista(OBRAS, 'art.html')})

    elif activa == 'shop.html':
        nodos.append({'@type': 'CollectionPage', '@id': canon + '#pagina',
                      'url': canon, 'name': 'Shop',
                      'isPartOf': {'@id': SITIO + '/#sitio'},
                      'mainEntity': lista(TIENDA + [MEDIAS], 'shop.html')})

    elif activa == 'contact.html':
        nodos.append({'@type': 'ContactPage', '@id': canon + '#pagina',
                      'url': canon, 'isPartOf': {'@id': SITIO + '/#sitio'},
                      'about': {'@id': SITIO + '/#judasaca'}})

    else:
        return ''

    bloque = json.dumps({'@context': 'https://schema.org', '@graph': nodos},
                        ensure_ascii=False, indent=1)
    return f'<script type="application/ld+json">\n{bloque}\n</script>\n'


def cabeza(titulo, desc, activa, og='img/oil-city-woodstock-sm.webp'):
    canon = SITIO + ('/' if activa == 'index.html' else '/' + activa)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="JUDASACA">
<meta property="og:title" content="{html.escape(titulo)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITIO}/{og}">
<meta name="twitter:card" content="summary_large_image">
{datos(activa, canon)}<link rel="icon" href="img/judasaca-logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

<header>
  <div class="barra">
    <button class="trazo" id="abrir-menu" aria-label="Menu" aria-expanded="false">
      <svg viewBox="0 0 30 22" aria-hidden="true" width="21" height="15">
        <path d="M2.4 4.1c6.1-1.2 15.7-1.5 25.2.3"/>
        <path d="M3.1 11c7.6-.9 14.9-.7 23.8.4"/>
        <path d="M2.7 17.9c5.3-1.3 14.4-1.4 24.6.2"/>
      </svg>
    </button>
    <a class="marca" href="index.html" aria-label="JUDASACA, home">
      <img src="img/judasaca-logo.png" alt="JUDASACA" width="900" height="673">
    </a>
    <button class="carro" id="carro" aria-label="Cart">
      <svg viewBox="0 0 24 24" aria-hidden="true" width="16" height="16"><circle cx="9" cy="20" r="1.3"/><circle cx="18" cy="20" r="1.3"/><path d="M1 2h3.4l2.6 12.4h11.6L22 6H6"/></svg>
      <span class="n" id="carro-n">0</span>
    </button>
  </div>
</header>

<aside class="menu-panel" id="menu-panel" aria-label="Menu" aria-hidden="true">
  <button class="x" id="cerrar-menu" aria-label="Close">&times;</button>
  <nav id="nav">
      {nav(activa)}
  </nav>
  <div class="abajo">
    Bogotá, Colombia<br>
    <a href="mailto:{CORREO}">{CORREO}</a><br>
    <a href="{IG}" rel="noopener">@judasaca</a>
  </div>
</aside>
'''


# Las vendidas quedan fuera del catalogo del carrito. Asi, si alguien tenia una
# guardada en su navegador de antes, desaparece sola la proxima vez que entre.
# Arte, tienda y medias comparten carrito: quien se lleva un cuadro de 1.950
# puede sumarle unas medias de 30 en la misma orden.
VENDIBLE = OBRAS + TIENDA + [MEDIAS]

CATALOGO = json.dumps({o['slug']: {'t': o['titulo'], 'm': o['med'], 'usd': o['usd']}
                       for o in VENDIBLE if not o['vendida']}, ensure_ascii=False)

DISPONIBLES = sum(1 for o in OBRAS if not o['vendida'] and not o.get('proxima'))
# Las vendidas se van al final sin perder el orden entre ellas: quien llega a
# la pagina ve primero lo que si puede comprar.
OBRAS_ORDEN = sorted(OBRAS, key=lambda o: o['vendida'])
EN_TIENDA   = sum(1 for o in TIENDA if not o['vendida'])

PIE = f'''
<footer>
  <div class="wrap pie">
    <div class="col"><b>Artwork</b>
      <a href="art.html">Original works</a>
      <a href="shop.html">Shop</a>
      <a href="cv.html">CV</a>
    </div>
    <div class="col"><b><a class="tit-enlace" href="{IG_ESTUDIO}" target="_blank"
      rel="noopener">303 Studio</a></b>
      <a href="about.html">About the artist</a>
      <a href="contact.html">Contact</a>
      <a href="mailto:{CORREO}">{CORREO}</a>
    </div>
    <div class="col"><b>Follow</b>
      <a href="{IG}" target="_blank" rel="noopener">Instagram · @judasaca</a>
      <a href="{TIKTOK}" target="_blank" rel="noopener">TikTok · @judasaca</a>
      <a href="{IG_ESTUDIO}" target="_blank" rel="noopener">Instagram · @303artstudio</a>
    </div>
    <div class="col fin">JUDASACA · Juan Salazar<br>Bogotá, Colombia<br>
      <span style="opacity:.7">nothing stays the same</span>
      <!-- Dice solo lo que es verdad. El pago ocurre dentro de la pasarela de
           Bold, no en esta pagina, asi que el numero de la tarjeta no pasa por
           aqui ni queda en ningun sitio nuestro. No se reclama ninguna
           certificacion que no tengamos. -->
      <span class="seguro">Payments are processed by Bold.<br>
        Card details are entered on Bold's gateway and never pass through this site.<br>
        <a href="privacy.html">Privacy</a></span></div>
  </div>
</footer>

<div class="velo" id="velo"></div>
<aside class="panel" id="panel" aria-label="Cart" aria-hidden="true">
  <div class="alto"><h2>Selected works</h2><button class="x" id="cerrar-carro" aria-label="Close">&times;</button></div>
  <div class="lista" id="carro-lista"></div>
  <div class="bajo">
    <div class="total"><span>Total</span><span id="carro-total">USD 0</span></div>
    <div class="pagar-carro" id="carro-pagar"></div>
    <button class="btn lleno" id="carro-pedir" type="button">Checkout</button>
    <p class="nota" id="carro-nota">Payment opens on Bold's gateway. Card details are
      entered there and never pass through this site. We ask where to ship afterwards.</p>
  </div>
</aside>

<div class="lupa" id="lupa" role="dialog" aria-modal="true" aria-label="Artwork">
  <button class="cerrar" aria-label="Close">&times;</button>
  <button class="pasar ant" aria-label="Previous">&#8249;</button>
  <button class="pasar sig" aria-label="Next">&#8250;</button>
  <div class="contador" id="lupa-n"></div>
  <figure><img id="lupa-img" alt="" draggable="false"><figcaption id="lupa-pie"></figcaption></figure>
  <div class="gesto">Swipe to browse · pinch or double tap to zoom</div>
</div>

<script>
/* Menu de celular y lupa de obras. Si el JavaScript falla, los enlaces de las
   obras siguen abriendo la imagen grande por su cuenta. */
(function(){{
  var b=document.getElementById('abrir-menu'), p=document.getElementById('menu-panel'),
      v=document.getElementById('velo'), x=document.getElementById('cerrar-menu');
  if(!b||!p) return;
  function abrir(){{ p.classList.add('abierto'); v.classList.add('abierto');
    p.setAttribute('aria-hidden','false'); b.setAttribute('aria-expanded','true');
    document.body.style.overflow='hidden'; x.focus(); }}
  function cerrar(){{ p.classList.remove('abierto'); v.classList.remove('abierto');
    p.setAttribute('aria-hidden','true'); b.setAttribute('aria-expanded','false');
    document.body.style.overflow=''; b.focus(); }}
  b.addEventListener('click', abrir);
  x.addEventListener('click', cerrar);
  v.addEventListener('click', cerrar);
  document.addEventListener('keydown', function(e){{
    if(e.key==='Escape' && p.classList.contains('abierto')) cerrar(); }});
}})();

(function(){{
  var enlaces=[].slice.call(document.querySelectorAll('[data-lupa]'));
  if(!enlaces.length) return;
  var caja=document.getElementById('lupa'), img=document.getElementById('lupa-img'),
      pie=document.getElementById('lupa-pie'), cont=document.getElementById('lupa-n'),
      i=0, antes=null;

  /* Estado del gesto. 'e' es la escala, 'x' e 'y' el desplazamiento dentro de
     la imagen cuando esta ampliada. */
  var e=1, x=0, y=0, px=0, py=0, pe=1, arrastra=false, pellizco=0, dedos={{}},
      partioEn=0, eje='', movido=false;

  function pinta(trans){{
    img.style.transition = trans ? 'transform .28s cubic-bezier(.2,.8,.3,1)' : 'none';
    img.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0) scale(' + e + ')';
  }}
  function reinicia(trans){{ e=1; x=0; y=0; pinta(trans); caja.classList.remove('ampliada'); }}

  /* Las vecinas se piden por adelantado: al deslizar, la siguiente ya esta. */
  function precarga(n){{
    [n-1, n+1].forEach(function(k){{
      var a=enlaces[(k+enlaces.length)%enlaces.length];
      if(a){{ var im=new Image(); im.src=a.getAttribute('href'); }}
    }});
  }}

  function mostrar(n, dir){{
    i=(n+enlaces.length)%enlaces.length;
    var a=enlaces[i];
    if(dir){{
      img.style.transition='none';
      img.style.opacity='0';
      img.style.transform='translate3d(' + (dir*40) + 'px,0,0)';
    }}
    img.src=a.getAttribute('href');
    img.alt=a.getAttribute('data-tit');
    pie.textContent=a.getAttribute('data-tit')+' · '+a.getAttribute('data-fic');
    if(cont) cont.textContent=(i+1)+' / '+enlaces.length;
    reinicia(false);
    requestAnimationFrame(function(){{
      img.style.transition='transform .3s cubic-bezier(.2,.8,.3,1),opacity .22s';
      img.style.opacity='1'; img.style.transform='translate3d(0,0,0) scale(1)';
    }});
    precarga(i);
  }}

  function abrir(n,orig){{
    antes=orig; mostrar(n);
    caja.classList.add('viendo');
    document.body.style.overflow='hidden';
    caja.querySelector('.cerrar').focus();
  }}
  function cerrar(){{
    caja.classList.remove('viendo','ampliada');
    document.body.style.overflow='';
    reinicia(false);
    if(antes) antes.focus();
  }}

  /* ── Gestos ────────────────────────────────────────────────────────────
     Un dedo: si la obra esta a tamano normal, arrastrar de lado pasa a la
     siguiente y arrastrar hacia abajo cierra. Si esta ampliada, arrastrar
     mueve la imagen. Dos dedos: pellizco para acercar.
     Doble toque: acerca y aleja en el punto tocado. */
  function dist(a,b){{ return Math.hypot(a.x-b.x, a.y-b.y); }}
  function dedosArr(){{ return Object.keys(dedos).map(function(k){{ return dedos[k]; }}); }}

  img.addEventListener('pointerdown', function(ev){{
    img.setPointerCapture(ev.pointerId);
    dedos[ev.pointerId]={{x:ev.clientX, y:ev.clientY}};
    var d=dedosArr();
    if(d.length===1){{
      arrastra=true; movido=false; eje='';
      px=ev.clientX-x; py=ev.clientY-y; partioEn=ev.clientX;
    }} else if(d.length===2){{
      arrastra=false; pellizco=dist(d[0],d[1]); pe=e;
    }}
  }});

  img.addEventListener('pointermove', function(ev){{
    if(!dedos[ev.pointerId]) return;
    dedos[ev.pointerId]={{x:ev.clientX, y:ev.clientY}};
    var d=dedosArr();

    if(d.length===2 && pellizco){{
      e=Math.min(5, Math.max(1, pe * dist(d[0],d[1]) / pellizco));
      caja.classList.toggle('ampliada', e>1.02);
      pinta(false); return;
    }}
    if(!arrastra) return;
    ev.preventDefault();
    var dx=ev.clientX-px-x, dy=ev.clientY-py-y;

    if(e>1.02){{ x=ev.clientX-px; y=ev.clientY-py; pinta(false); movido=true; return; }}

    /* A tamano normal el primer movimiento decide el eje, para que al deslizar
       de lado no se dispare el cierre y al revés tampoco. */
    if(!eje && (Math.abs(dx)>6 || Math.abs(dy)>6))
      eje = Math.abs(dx)>Math.abs(dy) ? 'h' : 'v';
    if(eje==='h'){{ x=ev.clientX-px; y=0; }}
    else if(eje==='v'){{ y=Math.max(0, ev.clientY-py); x=0; e=Math.max(.85, 1-y/900); }}
    movido=true; pinta(false);
  }}, {{passive:false}});

  function suelta(ev){{
    delete dedos[ev.pointerId];
    var quedan=dedosArr().length;
    if(quedan===1){{ var d=dedosArr()[0]; px=d.x-x; py=d.y-y; arrastra=true; eje=''; }}
    if(quedan>0){{ pellizco=0; return; }}
    arrastra=false; pellizco=0;
    if(e>1.02){{ caja.classList.add('ampliada'); return; }}

    if(eje==='h' && Math.abs(x)>70){{ mostrar(i + (x<0?1:-1), x<0?1:-1); eje=''; return; }}
    if(eje==='v' && y>110){{ cerrar(); return; }}
    eje=''; reinicia(true);
  }}
  img.addEventListener('pointerup', suelta);
  img.addEventListener('pointercancel', suelta);

  var ultimoToque=0;
  img.addEventListener('click', function(ev){{
    var ahora=Date.now();
    if(movido){{ movido=false; return; }}
    if(ahora-ultimoToque<300){{
      if(e>1.02){{ reinicia(true); }}
      else{{
        var r=img.getBoundingClientRect();
        e=2.6;
        x=(r.left+r.width/2-ev.clientX)*(e-1);
        y=(r.top+r.height/2-ev.clientY)*(e-1);
        caja.classList.add('ampliada'); pinta(true);
      }}
    }}
    ultimoToque=ahora;
  }});

  /* La rueda del mouse tambien acerca, para quien esta en computador. */
  img.addEventListener('wheel', function(ev){{
    if(!caja.classList.contains('viendo')) return;
    ev.preventDefault();
    e=Math.min(5, Math.max(1, e - ev.deltaY*0.0022));
    if(e<=1.02){{ reinicia(false); }} else {{ caja.classList.add('ampliada'); pinta(false); }}
  }}, {{passive:false}});

  enlaces.forEach(function(a,n){{
    a.addEventListener('click',function(ev){{ ev.preventDefault(); abrir(n,a); }});
  }});
  caja.querySelector('.cerrar').addEventListener('click',cerrar);
  caja.querySelector('.ant').addEventListener('click',function(){{ mostrar(i-1,-1); }});
  caja.querySelector('.sig').addEventListener('click',function(){{ mostrar(i+1, 1); }});
  caja.addEventListener('click',function(ev){{ if(ev.target===caja) cerrar(); }});
  document.addEventListener('keydown',function(ev){{
    if(!caja.classList.contains('viendo')) return;
    if(ev.key==='Escape') cerrar();
    if(ev.key==='ArrowLeft') mostrar(i-1,-1);
    if(ev.key==='ArrowRight') mostrar(i+1, 1);
    if(ev.key==='0') reinicia(true);
  }});
}})();

/* ── Carrito ──────────────────────────────────────────────────────────
   Guarda lo elegido en el propio navegador y arma un correo con la lista.
   No cobra nada todavia: cuando existan los enlaces de pago de Stripe,
   este mismo carrito puede mandar al checkout. */
(function(){{
  var CAT = {CATALOGO};
  var LLAVE='judasaca-carro';
  var carro=[];
  try{{ carro=JSON.parse(localStorage.getItem(LLAVE)||'[]'); }}catch(e){{ carro=[]; }}
  carro = carro.filter(function(s){{ return CAT[s]; }});

  var bot=document.getElementById('carro'), num=document.getElementById('carro-n'),
      panel=document.getElementById('panel'), velo=document.getElementById('velo'),
      lista=document.getElementById('carro-lista'), total=document.getElementById('carro-total'),
      pedir=document.getElementById('carro-pedir'), nota=document.getElementById('carro-nota');
  if(!bot||!panel) return;

  function guardar(){{ try{{ localStorage.setItem(LLAVE, JSON.stringify(carro)); }}catch(e){{}} }}
  function dinero(n){{ return 'USD ' + n.toLocaleString('en-US'); }}

  function pintar(){{
    num.textContent = carro.length;
    if(!carro.length){{
      lista.innerHTML = '<p class="vacio">Nothing selected yet.</p>';
      total.textContent = dinero(0);
      pedir.disabled = true;
      return;
    }}
    pedir.disabled = false;
    var suma = 0, h = '';
    carro.forEach(function(sl){{
      var o = CAT[sl]; suma += o.usd;
      h += '<div class="item"><img src="img/'+sl+'-sm.webp" alt="">'
        +  '<div class="d"><div class="t">'+o.t+'</div>'
        +  '<div class="f">'+o.m+'</div>'
        +  '<div class="p">'+dinero(o.usd)+'</div>'
        +  '<button class="quitar" data-q="'+sl+'">Remove</button></div></div>';
    }});
    lista.innerHTML = h;
    total.textContent = dinero(suma);
  }}

  /* Checkout de verdad: el carrito cobra, no manda un correo. Se firma la
     lista contra el Worker (que suma el total y decide el precio) y se abre
     Bold por el total, en una sola orden. */
  function cobrar(){{
    if (!carro.length || !window.fetch || !window.JUDPAGO) return;
    pedir.disabled = true;
    pedir.textContent = 'One moment…';

    fetch('{FIRMADOR}/firma', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ modo: 'carro', slugs: carro }})
    }})
    .then(function(r){{ return r.json(); }})
    .then(function(d){{
      if (!d || !d.carro) throw new Error('sin-orden');

      // Si algo se vendio mientras el comprador miraba, el Worker lo deja
      // fuera de la firma. Se le dice, se le quita del carrito y se cobra lo
      // que si esta: nadie paga por un cuadro que ya no existe.
      var firmadas = d.carro.slugs || [];
      var caidas = carro.filter(function(s){{ return firmadas.indexOf(s) < 0; }});
      if (caidas.length) {{
        carro = firmadas.slice();
        guardar(); pintar();
        nota.textContent = caidas.length === 1
          ? CAT[caidas[0]].t + ' was just sold and has been removed. Paying for the rest.'
          : caidas.length + ' works were just sold and have been removed. Paying for the rest.';
        nota.className = 'nota aviso';
      }}

      pedir.style.display = 'none';
      window.JUDPAGO.abrir(document.getElementById('carro-pagar'), d.carro, location.href);
    }})
    .catch(function(){{
      pedir.disabled = false;
      pedir.textContent = 'Checkout';
      nota.className = 'nota aviso';
      nota.innerHTML = 'Checkout is not responding. Write to '
        + '<a href="mailto:{CORREO}">{CORREO}</a> and Juan will take it from there.';
    }});
  }}

  function abrir(){{ panel.classList.add('abierto'); velo.classList.add('abierto');
    panel.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; }}
  function cerrar(){{ panel.classList.remove('abierto'); velo.classList.remove('abierto');
    panel.setAttribute('aria-hidden','true'); document.body.style.overflow=''; }}

  bot.addEventListener('click', function(){{ pintar(); abrir(); }});
  pedir.addEventListener('click', cobrar);
  velo.addEventListener('click', cerrar);
  document.getElementById('cerrar-carro').addEventListener('click', cerrar);
  document.addEventListener('keydown', function(e){{
    if(e.key==='Escape' && panel.classList.contains('abierto')) cerrar(); }});

  lista.addEventListener('click', function(e){{
    var q=e.target.getAttribute && e.target.getAttribute('data-q');
    if(!q) return;
    carro = carro.filter(function(s){{ return s!==q; }});
    guardar(); pintar();
  }});

  document.querySelectorAll('.add').forEach(function(b){{
    b.addEventListener('click', function(){{
      var sl=b.getAttribute('data-slug');
      if(carro.indexOf(sl)<0) carro.push(sl);
      guardar(); pintar(); abrir();
    }});
  }});

  pintar();
}})();

/* ── Pago ───────────────────────────────────────────────────────────────
   Un solo motor de pago para toda la pagina: lo usan los botones Buy de cada
   obra y tambien el carrito.

   Flujo, corto a proposito: clic en Buy -> la pasarela de Bold se abre encima
   del sitio -> paga. Nada de formularios antes. La direccion de envio se pide
   DESPUES, en la pagina de gracias, cuando la plata ya entro y el comprador
   no puede arrepentirse a mitad de camino por tener que teclear.

   El navegador NUNCA manda el precio: manda slugs, y el Worker decide cuanto
   se cobra y lo firma. Un precio que mande el atacante no vale nada aunque
   venga firmado, porque estaria firmando su propia mentira. */
window.JUDPAGO = (function(){{
  var libreria = null, abriendo = false;

  /* Devuelve una promesa que solo se cumple cuando la libreria esta lista de
     verdad. Se guarda para que dos clics no la carguen dos veces. */
  function cargarLibreria(){{
    if (libreria) return libreria;
    libreria = new Promise(function(ok, mal){{
      if (window.BoldCheckout) return ok();
      var s = document.createElement('script');
      s.src = 'https://checkout.bold.co/library/boldPaymentButton.js';
      s.onload = function(){{ window.BoldCheckout ? ok() : mal(); }};
      s.onerror = mal;
      document.head.appendChild(s);
    }});
    return libreria;
  }}

  /* Se recuerda la orden para que la pagina de gracias sepa que se acaba de
     pagar: ahi se le pide la direccion y se marcan las obras como vendidas. */
  function recordar(orden){{
    try {{
      localStorage.setItem('judasaca-orden', JSON.stringify({{
        id: orden.orderId,
        slugs: orden.slugs || [],
        amount: orden.amount,
        description: orden.description,
        t: Date.now()
      }}));
    }} catch(e) {{}}
  }}

  /* Abre la pasarela directamente, sin dibujar ningun boton de Bold.

     Antes esto inyectaba un <script data-bold-button> y luego le hacia clic
     solo. Eso era una carrera perdida: la libreria de Bold busca esos scripts
     cuando ELLA carga, asi que segun quien llegara primero unas veces salia el
     boton y otras veces no salia nada. Con la API (new BoldCheckout().open())
     no hay nada que esperar ni nada que adivinar: se abre y ya. */
  function abrir(destino, orden, origen){{
    if (abriendo) return;
    abriendo = true;
    recordar(orden);

    cargarLibreria().then(function(){{
      new window.BoldCheckout({{
        orderId: orden.orderId,
        currency: orden.currency,
        amount: orden.amount,
        apiKey: '{LLAVE_IDENTIDAD}',
        integritySignature: orden.signature,
        description: orden.description,
        redirectionUrl: '{SITIO}/thanks.html',
        originUrl: origen || '{SITIO}/art.html',
        // Embedded: la pasarela abre encima del sitio y el comprador no se va.
        renderMode: 'embedded'
      }}).open();
      abriendo = false;
    }}).catch(function(){{
      abriendo = false;
      if (destino) {{
        destino.innerHTML = '<span class="fallo">Checkout could not open. '
          + 'Write to <a href="mailto:{CORREO}">{CORREO}</a>.</span>';
      }}
    }});
  }}

  /* Una obra vendida se apaga entera: sello, ficha tachada y sin botones. */
  function marcarVendidas(lista){{
    (lista || []).forEach(function(slug){{
      var hueco = document.querySelector('.pagar[data-obra="' + slug + '"]');
      if (!hueco) return;
      var obra = hueco.closest('.obra');
      if (!obra || obra.classList.contains('agotada')) return;
      obra.classList.add('agotada');
      var marco = obra.querySelector('.marco');
      if (marco && !marco.querySelector('.sello')) {{
        marco.classList.add('vendido');
        var s = document.createElement('span');
        s.className = 'sello';
        s.setAttribute('aria-hidden', 'true');
        s.innerHTML = '<i></i><b>Sold</b><i></i>';
        marco.appendChild(s);
      }}
      var acciones = obra.querySelector('.acciones');
      if (acciones) acciones.innerHTML = '<span class="sello-vendida">Sold</span>';
    }});
  }}

  return {{ abrir: abrir, marcarVendidas: marcarVendidas, firmador: '{FIRMADOR}' }};
}})();

/* ── Buy en cada obra ───────────────────────────────────────────────────
   Solo corre en paginas con huecos .pagar (hoy, la de obras). */
(function(){{
  var huecos = [].slice.call(document.querySelectorAll('.pagar[data-obra]'));
  if (!huecos.length || !window.fetch) return;

  var slugs = huecos.map(function(h){{ return h.getAttribute('data-obra'); }});
  var firmadas = {{}};   // slug -> orden ya firmada por el Worker

  function firmar(lista){{
    return fetch('{FIRMADOR}/firma', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ slugs: lista }})
    }}).then(function(r){{ return r.json(); }});
  }}

  /* Precarga. Corre al cargar la pagina y suele llegar antes de que nadie
     haga clic, asi que el boton abre Bold de una. Si Cloudflare esta frio y
     tarda, no importa: el boton ya esta pintado y el clic firma solo. */
  firmar(slugs).then(function(d){{
    if (d && d.vendidas) window.JUDPAGO.marcarVendidas(d.vendidas);
    if (d && d.obras) firmadas = d.obras;
  }}).catch(function(){{ }});

  function abrirObra(boton, slug){{
    var hueco = boton.parentNode;
    boton.disabled = true;
    boton.textContent = 'Opening…';

    var orden = firmadas[slug];
    if (orden) {{
      orden.slugs = [slug];
      window.JUDPAGO.abrir(hueco, orden, location.href);
      return;
    }}
    // Todavia no habia llegado la precarga: se firma esta sola y se abre.
    firmar([slug]).then(function(d){{
      if (d && d.vendidas) window.JUDPAGO.marcarVendidas(d.vendidas);
      var o = d && d.obras && d.obras[slug];
      if (!o) throw new Error('sin-orden');
      firmadas[slug] = o;
      o.slugs = [slug];
      window.JUDPAGO.abrir(hueco, o, location.href);
    }}).catch(function(){{
      boton.disabled = false;
      boton.textContent = 'Buy';
      hueco.insertAdjacentHTML('beforeend',
        '<span class="fallo">Could not open checkout. '
        + 'Write to <a href="mailto:{CORREO}">{CORREO}</a>.</span>');
    }});
  }}

  document.addEventListener('click', function(e){{
    var b = e.target.closest && e.target.closest('.pagar .comprar');
    if (!b || b.disabled) return;
    abrirObra(b, b.getAttribute('data-obra'));
  }});
}})();
</script>
</body>
</html>
'''


def ver(ruta):
    """Le pega a la imagen una firma corta de su propio contenido.

    El problema: cuando se cambia una foto sin cambiarle el nombre, el
    navegador sigue mostrando la vieja porque cree que ya la tiene. Con la
    firma detras, cambiar la foto cambia la direccion, y el navegador la pide
    de nuevo sola. Si la foto no cambia, la firma tampoco y se sigue
    aprovechando la copia guardada, que es justo lo que uno quiere.
    """
    entera = os.path.join(RUTA, ruta)
    if not os.path.exists(entera):
        return ruta
    with open(entera, 'rb') as fh:
        firma = hashlib.sha1(fh.read()).hexdigest()[:8]
    return f'{ruta}?v={firma}'


def tarjeta_obra(o, mini=True):
    # La obra panoramica ocupa la fila entera, asi que en pantalla grande se
    # muestra a mas de 1200 px. La version pequena es de 700 y se veria estirada:
    # esa se lleva la imagen grande.
    if o.get('ancha'):
        img = ver(f"img/{o['slug']}.webp")
    else:
        img = ver(f"img/{o['slug']}-sm.webp") if mini else ver(f"img/{o['slug']}.webp")
    # Una obra vendida ya no lleva precio. Lo pidieron asi y tiene sentido:
    # el precio de algo que no se puede comprar solo invita a preguntar por
    # que, y a comparar la obra que uno si puede comprar contra una que no.
    if o.get('proxima'):
        precio = '<span class="p proxima">Coming soon</span>'
    elif o['vendida']:
        precio = ''
    else:
        precio = f'<span class="p">USD {o["usd"]:,}</span>'
    # Hueco donde el JavaScript inserta el boton de Bold una vez el Worker
    # devuelve la firma. Toda obra que no este vendida lo lleva: quien quiere
    # comprar compra, sin pasos de por medio y sin pedir permiso por correo.
    # El boton va escrito en el HTML, no lo crea el JavaScript. Antes se creaba
    # al volver el fetch al Worker, asi que en un arranque en frio de Cloudflare
    # la obra se quedaba varios segundos sin boton y parecia que no se vendia.
    # Ahora esta desde el primer pintado; la firma se pide al hacer clic si el
    # precargado todavia no llego.
    comprar = ('' if o['vendida'] or o.get('proxima') else
               f'<span class="pagar" data-obra="{o["slug"]}">'
               f'<button class="btn lleno comprar" type="button" '
               f'data-obra="{o["slug"]}">Buy</button></span>')
    carrito = ('' if o['vendida'] or o.get('proxima') else
               f'<button class="btn add" data-slug="{o["slug"]}">Add to cart</button>')

    # Vendida: se va todo lo que invita a comprar y queda el sello. Dos rayas
    # rojas en diagonal con la palabra en medio, y la ficha en gris tachada.
    if o.get('proxima'):
        acciones, sello, clase_obra, clase_marco = '', '', '', ' proximo'
    elif o['vendida']:
        acciones = '<span class="sello-vendida">Sold</span>'
        sello = '<span class="sello" aria-hidden="true"><i></i><b>Sold</b><i></i></span>'
        clase_obra, clase_marco = ' agotada', ' vendido'
    else:
        acciones = f'{comprar}{carrito}'
        sello, clase_obra, clase_marco = '', '', ''

    # Una obra puede traer 'nota': hoy la usa Rendered Reality para decir
    # donde se expuso. Va debajo de la ficha, en chico.
    nota = ('\n            <div class="expo">' + html.escape(o['nota']) + '</div>'
            if o.get('nota') else '')

    if o.get('recorte'):
        clase_marco += ' recorte'
    # Una obra panoramica ocupa dos celdas de la reja y su marco deja de ser
    # cuadrado. Asi se ve a su proporcion, sin franjas de relleno.
    if o.get('ancha'):
        clase_obra += ' ancha'

    # 'fondo' quedo de cuando las fichas no eran cuadradas y sobraban franjas.
    # Hoy no sobra ninguna, pero se deja el mecanismo por si entra una foto
    # con otra proporcion: si la obra trae fondo, el marco se pinta de ese color.
    est = f' style="background:{o["fondo"]}"' if o.get('fondo') else ''

    return f'''      <article class="obra{clase_obra}">
        <figure>
          <a class="marco{clase_marco}"{est} href="{ver(f"img/{o['slug']}.webp")}"
             data-lupa data-tit="{html.escape(o['titulo'])}"
             data-fic="{html.escape(o['tec'])} · {o['med']}">
            <img src="{img}" alt="{html.escape(o['titulo'])}, {html.escape(o['tec'].lower())}, {o['med']}" loading="lazy">{sello}
          </a>
          <figcaption>
            <div class="linea"><span class="t">{html.escape(o['titulo'])}</span>
              <span class="f">· {o['med']} ·</span> {precio}</div>{nota}
            <div class="acciones">{acciones}</div>
          </figcaption>
        </figure>
      </article>
'''


def tira(slugs, destino, fuente):
    """Tres miniaturas que llevan a la otra pagina.

    Lo estrenamos en la tienda para mandar a la pagina de arte y funciono, asi
    que la pagina de arte tambien manda a la tienda. Una imagen invita a
    entrar; un enlace de texto se ignora.
    """
    por_slug = {o['slug']: o for o in fuente}
    return ''.join(
        f'''          <a class="lienzo" href="{destino}">
            <img src="{ver(f"img/{s}-sm.webp")}" alt="{html.escape(por_slug[s]["titulo"])}" loading="lazy">
          </a>
''' for s in slugs if s in por_slug)


def escribir(nombre, cuerpo):
    # Se escribe a un temporal y se renombra encima, en vez de abrir el archivo
    # final en modo 'w'. Dos razones: en carpetas sincronizadas (iCloud, Drive)
    # abrir en 'w' un archivo que el sistema tiene tomado revienta con
    # "Resource deadlock avoided", y ademas asi la escritura es atomica: si el
    # build falla a medias, nunca queda una pagina cortada en el sitio.
    ruta = os.path.join(RUTA, nombre)
    tmp = ruta + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(cuerpo)
    os.replace(tmp, ruta)
    return len(cuerpo)


# ══════════════════════════════════════════════════════════════════════════
# 1 · HOME
# ══════════════════════════════════════════════════════════════════════════
destacadas = [o for o in OBRAS if o['slug'] in
              ('sunday-snoops', 'nothing-stays-the-same', 'blue-thoughts-rat')]

home = cabeza(
  'JUDASACA · Juan Salazar · Hybrid artist, Bogotá',
  'Colombian hybrid artist working between painting and augmented reality. '
  'Original works, exhibitions and contact.',
  'index.html') + f'''
<main>
  <div class="wrap">
    <div class="hero">
      <h1>nothing stays the same</h1>
    </div>

    <div class="portada-obra">
      <img src="intro_photo.webp"
           alt="Juan Salazar, JUDASACA">
      <div class="pie-obra">Juan Salazar</div>
    </div>

    <div class="entrada-home">
      <p>Juan Salazar paints the characters that raised us, then lets technology pull them
        out of shape. Traditional canvas, augmented reality, and the question of what a
        brand really owns once it has lived inside your childhood.</p>
      <a class="btn" href="art.html">See the work</a>
    </div>
  </div>
</main>
''' + PIE

# ══════════════════════════════════════════════════════════════════════════
# 2 · ABOUT
# ══════════════════════════════════════════════════════════════════════════
prensa_html = '\n'.join(
  f'''        <a href="{u}" rel="noopener">
          <div class="medio">{html.escape(m)}</div>
          <div class="titular">{html.escape(t)}</div>
        </a>''' for m, t, u in PRENSA)

about = cabeza(
  'About · JUDASACA · Juan Salazar',
  'Juan Salazar, known as JUDASACA, is a Colombian hybrid artist working between '
  'traditional painting and augmented reality.',
  'about.html', og='about_photo.webp') + f'''
<main>
  <section>
    <div class="wrap">
      <div class="tit centrado"><div class="eti">About</div><h2>Juan Salazar</h2></div>
      <div class="dos">
        <!-- La foto se queda quieta mientras el texto corre. Es el gesto mas caro
             que se puede hacer sin agregar un solo elemento a la pagina. -->
        <div class="foto">
          <img class="retrato" src="about_photo.webp"
               alt="Juan Salazar painting a mural, Bogotá">
          <figcaption class="pie-foto">Studio, Bogotá</figcaption>
        </div>
        <div class="prosa vida">
          <p class="entrada">JUDASACA is a hybrid artist. He paints on canvas, and then
            <span class="mueve">he lets the painting move.</span></p>

          <p>Juan Salazar spent more than fifteen years in marketing and international
            business before art became the work rather than the thing beside it. His
            artistic career began in 2018, though some collectors trace his earliest
            pieces back to 2014. The turn came during a master's degree in Barcelona,
            where the artists around him made the decision look obvious. He returned to
            Bogotá, found the San Felipe art district, and started showing.</p>

          <p>In 2021 he exhibited internationally for the first time and ran into crypto
            art. His first NFT collection, five editions, sold in under a day. By early
            2023 his work was on the screens of Times Square. Since then it has travelled
            to New York, Miami, Tokyo, Lisbon, Barcelona, Mexico City, Costa Rica and Lima.</p>

          <h3>Brandalism</h3>
          <p>He paints the characters that raised a generation: Snoopy, Woodstock, Mickey.
            He takes them out of the stories they belong to and puts them somewhere less
            comfortable. The work asks what a brand actually owns once it has lived inside
            your childhood, and what is left of you when you notice the icons have aged too.</p>

          <p>The other half is technology. He has spent years building augmented and virtual
            layers over his paintings, so that a fixed canvas becomes something that will not
            hold still. That is the whole argument in one gesture: nothing stays the same. He
            is a member of One Love ArtDAO, co-founder of the
            artist collective The Art Cartel alongside Yuseph Zapata and Lucas Zapata, and
            helped build Chromaverse, a platform for showing work in physical and virtual
            galleries at once.</p>

          <blockquote class="cita">
            “I play with art and technology to create experiences that go beyond the canvas.”
            <cite>Juan Salazar, interviewed by ColombiaOne, October 2025</cite>
          </blockquote>

          <p>He has spoken at NFT NYC in 2024, 2025 and 2026. He lives and works in Bogotá.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="humo">
    <div class="wrap">
      <div class="tit"><div class="eti">Press</div><h2>Written about</h2></div>
      <div class="prensa">
{prensa_html}
      </div>
    </div>
  </section>
</main>
''' + PIE

# ══════════════════════════════════════════════════════════════════════════
# 3 · ART
# ══════════════════════════════════════════════════════════════════════════
art = cabeza(
  'Original works · JUDASACA',
  f'{DISPONIBLES} original paintings by JUDASACA, available now. Acrylics, oil and spray '
  'on canvas. Bogotá, Colombia.',
  'art.html') + f'''
<main>
  <section>
    <div class="wrap">
      <div class="tit">
        <div class="eti">Original works · {DISPONIBLES} available</div>
        <h2>Art</h2>
        <p>Every piece here is a single original, painted by hand and signed. Prices are
          in US dollars. Worldwide shipping and framing is not included.</p>
      </div>
      <div class="obras">
{''.join(tarjeta_obra(o) for o in OBRAS_ORDEN)}      </div>
    </div>
  </section>

  <section class="humo">
    <div class="wrap">
      <div class="tit">
        <div class="eti">Smaller work</div>
        <h2>Shop</h2>
      </div>
      <div class="lienzos">
{tira(['judasaca-socks', 'woodstocks-on-fire', 'out-in-the-beach-rat'], 'shop.html', TIENDA + [MEDIAS])}      </div>
      <p style="margin-top:26px"><a class="btn" href="shop.html">See the shop</a></p>
    </div>
  </section>

  <section>
    <div class="wrap estrecho prosa">
      <div class="tit"><div class="eti">Buying</div><h2>How it works</h2></div>
      <p>Works ship worldwide from Bogotá. Larger canvases usually travel rolled in a
        tube and are stretched on arrival, which is standard practice and keeps shipping
        sane.</p>

      <!-- Dicho en positivo, pero sin inventar nada. Cada frase de aqui es
           comprobable: el pago ocurre en la pasarela de Bold, el sitio va por
           HTTPS, y el monto se firma antes de salir. No se menciona ninguna
           certificacion que no sea nuestra. -->
      <h3>Paying securely</h3>
      <p>Payments are completed through Bold's payment gateway. We do not keep your card
        details. More on the <a href="privacy.html">privacy page</a>.</p>
    </div>
  </section>
</main>
''' + PIE

# ══════════════════════════════════════════════════════════════════════════
# 4 · SHOP
# ══════════════════════════════════════════════════════════════════════════
# Las tarjetas se arman con la misma funcion que el arte: mismo boton de Bold,
# mismo carrito, mismo sello de vendida. La tienda no es un sistema aparte.
tienda_html = ''.join(tarjeta_obra(o) for o in TIENDA)
medias_html = tarjeta_obra(MEDIAS)

# Tres lienzos de muestra para el bloque que lleva a la pagina de arte.
muestra_html = tira(['rendered-reality', 'oil-city-woodstock', 'city-famous-rat'],
                    'art.html', OBRAS)

shop = cabeza(
  'Shop · JUDASACA',
  'Socks, original works on paper and canvases by JUDASACA. Shipped worldwide.',
  'shop.html', og='img/judasaca-socks-sm.webp') + f'''
<main>

  <section>
    <div class="wrap">
      <div class="tit">
        <div class="eti">Merch</div>
        <h2>Broken Icon × Bitcoin Rat Socks</h2>
        <p>Two pairs, sold together, in a box built from the same two paintings.</p>
      </div>
      <div class="medias-prod">
{medias_html}      </div>
    </div>
  </section>

  <section class="humo">
    <div class="wrap">
      <div class="tit">
        <div class="eti">On paper</div>
        <h2>Art</h2>
      </div>
      <div class="obras">
{tienda_html}      </div>
    </div>
  </section>

  <section>
    <div class="wrap">
      <div class="tit">
        <div class="eti">On canvas</div>
        <h2>Canvases</h2>
      </div>
      <div class="lienzos">
{muestra_html}      </div>
      <p style="margin-top:26px"><a class="btn" href="art.html">See the canvases</a></p>
    </div>
  </section>

  <section class="humo">
    <div class="wrap">
      <div class="tit">
        <div class="eti">Prints</div>
        <h2>Prints</h2>
      </div>
      <div class="pronto">
        <h3>Coming soon</h3>
        <p>Editions of the works you have just seen, at a size and a price that fit a
          first wall. If you want to know the day they open, write and you will be told
          before anyone else.</p>
        <p style="margin-top:24px">
          <a class="btn" href="mailto:{CORREO}?subject=Prints%20—%20let%20me%20know%20when%20they%20open">Tell me when they open</a>
        </p>
      </div>
    </div>
  </section>

</main>
''' + PIE

# ══════════════════════════════════════════════════════════════════════════
# 5 · CV
# ══════════════════════════════════════════════════════════════════════════
def pais_de(lugar):
    """Nombre corto del pais, para filtrar. Bogota y Miami vienen sin pais."""
    for clave in PAISES:
        if clave in lugar:
            return clave
    if 'Bogotá' in lugar: return 'Colombia'
    if 'Miami' in lugar:  return 'USA'
    if 'digital' in lugar.lower(): return 'Digital'
    return 'Other'



def medidas_webp(ruta):
    """Ancho y alto de un .webp leyendo la cabecera, sin librerias de imagen.

    Se usa para decidir sola la forma de cada foto en la galeria: la vertical
    va alta, la horizontal va ancha. Asi Juan agrega una foto y no tiene que
    decir nada mas.
    """
    try:
        with open(ruta, 'rb') as f:
            d = f.read(40)
    except OSError:
        return (0, 0)
    if len(d) < 30 or d[:4] != b'RIFF' or d[8:12] != b'WEBP':
        return (0, 0)
    tipo = d[12:16]
    if tipo == b'VP8 ':
        return (int.from_bytes(d[26:28], 'little') & 0x3FFF,
                int.from_bytes(d[28:30], 'little') & 0x3FFF)
    if tipo == b'VP8L':
        b = int.from_bytes(d[21:25], 'little')
        return ((b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1)
    if tipo == b'VP8X':
        return (int.from_bytes(d[24:27], 'little') + 1,
                int.from_bytes(d[27:30], 'little') + 1)
    return (0, 0)


# Casi todas las fotos son verticales de celular. Si se respeta la proporcion
# y nada mas, la galeria queda como una tira de cine: quince rectangulos
# iguales en fila. El ritmo se arma entonces con el tamano y la altura a la
# que cuelga cada una, rotando cuatro variantes.
RITMO = ['alta', 'baja', 'xl', 'chica']

def forma_de(nombre, n=0):
    """La forma de la ficha en la galeria.

    Las horizontales de verdad van anchas; las verticales rotan por el ritmo.
    """
    an, al = medidas_webp(os.path.join(RUTA, 'img', nombre + '.webp'))
    if al and an / float(al) >= 1.20:
        return 'ancha'
    return RITMO[n % len(RITMO)]


def ciudad_de(lugar):
    """Ciudad reconocida dentro del texto del lugar, para poner el pin."""
    for c in mapa.CIUDADES:
        if c in lugar:
            return c
    if 'Bogotá' in lugar: return 'Bogotá'
    return ''


def mota(texto):
    """Ficha de puntos para la exposicion que no tiene foto.

    Se dibuja a partir del nombre, asi que cada una sale distinta y siempre la
    misma. Antes ahi quedaba un recuadro vacio y se veia como un error.
    """
    h = hashlib.sha1(texto.encode('utf-8')).digest()
    bits = ''.join(f'{b:08b}' for b in h)
    ptos = []
    for f in range(5):
        for c in range(5):
            if bits[f * 5 + c] == '1':
                ptos.append(f'<circle cx="{8 + c * 11}" cy="{8 + f * 11}" r="3.1"/>')
    return (f'<span class="mota" aria-hidden="true">'
            f'<svg viewBox="0 0 60 60">{"".join(ptos)}</svg></span>')


ROTULOS = {'solo':'Solo', 'duo':'Two-person', 'charla':'Talk', 'grupo':''}


def marcas_de(it):
    m = ''
    r = ROTULOS.get(it.get('tipo', 'grupo'), '')
    if r:
        m += f'<span class="tipo {it["tipo"]}">{r}</span>'
    if it.get('premio'):
        m += f'<span class="premio">{html.escape(it["premio"])}</span>'
    if it.get('estado') == 'upcoming':
        m += '<span class="pronto">Upcoming</span>'
    return m


def foto_rail(it, n):
    """Ficha del riel. Solo las que tienen foto.

    Las formas rotan para que el riel no parezca tira de cine: alta, grande,
    pequena colgada abajo, chica arriba. Es lo que le daba composicion a la
    primera version y lo que se perdio al meter todas las entradas aqui.
    """
    # Con pie: una foto sin nombre no sirve de nada, hay que poder decir que
    # muestra es sin abrirla. Va corto (nombre y ciudad) para que no compita
    # con la linea del listado, que lleva el dato completo.
    forma = forma_de(it['foto'], n)
    ciudad = ciudad_de(it['lugar']) or it['lugar'].split(',')[0]
    return (f'          <figure class="gfoto {forma}">'
            f'<a href="{ver("img/" + it["foto"] + ".webp")}" data-lupa '
            f'data-tit="{html.escape(it["nombre"])}" data-fic="{html.escape(it["lugar"])}">'
            f'<img src="{ver("img/" + it["foto"] + "-sm.webp")}" loading="lazy" '
            f'alt="{html.escape(it["nombre"])}, {html.escape(it["lugar"])}"></a>'
            f'<figcaption><b>{html.escape(it["nombre"])}</b>'
            f'<span>{html.escape(ciudad)}</span></figcaption></figure>')


def fila_expo(it):
    """Una linea del listado del anio. Texto, que es lo que debe ser.

    Meterla al riel como tarjeta la obligaba a inventarse una imagen. Como
    linea no le falta nada: dice que fue, donde, y de que clase.
    """
    return (f'          <li class="fila{" futuro" if it.get("estado")=="upcoming" else ""}" '
            f'data-pais="{html.escape(pais_de(it["lugar"]))}" '
            f'data-tipo="{it.get("tipo","grupo")}" '
            f'data-estado="{"upcoming" if it.get("estado")=="upcoming" else "past"}">'
            f'<span class="nom">{html.escape(it["nombre"])}</span>'
            f'<span class="lugar">{html.escape(it["lugar"])}</span>'
            f'<span class="etiquetas">{marcas_de(it)}</span></li>')


_nf = [0]

def bloque_anio(anio, items):
    conFoto = [i for i in items if i.get('foto')]
    rail = ''
    if conFoto:
        fichas = []
        for i in conFoto:
            fichas.append(foto_rail(i, _nf[0])); _nf[0] += 1
        rail = ('\n        <div class="riel-caja">\n        <div class="riel">\n'
                + '\n'.join(fichas) + '\n        </div>\n        </div>')
    n = len(items)
    return (f'      <div class="anio" data-anio="{anio}">\n'
            f'        <div class="anio-cab"><h3>{anio}</h3>'
            f'<span class="cuantas">{n} {"entry" if n == 1 else "entries"}</span></div>'
            f'{rail}\n'
            f'        <ul class="listado">\n'
            + '\n'.join(fila_expo(i) for i in items)
            + '\n        </ul>\n      </div>')


# Un chip por pais donde ha expuesto, ordenados por cuantas veces aparece.
_conteo = {}
for _a, _its in EXPOS:
    for _i in _its:
        _p = pais_de(_i['lugar'])
        _conteo[_p] = _conteo.get(_p, 0) + 1
_N_PROXIMAS = sum(1 for _a, _its in EXPOS for _i in _its if _i.get('estado') == 'upcoming')

_cuenta_tipo = {}
for _a, _its in EXPOS:
    for _i in _its:
        _t = _i.get('tipo', 'grupo')
        _cuenta_tipo[_t] = _cuenta_tipo.get(_t, 0) + 1

_chips = ['<button class="chip activo" data-filtro="todo" type="button">'
          f'All <i>{N_EXPOS}</i></button>']
# El orden importa: lo que mas pesa en una hoja de vida de artista va primero.
for _t, _r in (('solo','Solo'), ('duo','Two-person'), ('grupo','Group'), ('charla','Talks')):
    if _cuenta_tipo.get(_t):
        _chips.append(f'<button class="chip" data-tipo="{_t}" type="button">'
                      f'{_r} <i>{_cuenta_tipo[_t]}</i></button>')
if _N_PROXIMAS:
    _chips.append('<button class="chip" data-filtro="upcoming" type="button">'
                  f'Upcoming <i>{_N_PROXIMAS}</i></button>')
for _p, _n in sorted(_conteo.items(), key=lambda x: -x[1]):
    _chips.append(f'<button class="chip" data-pais="{html.escape(_p)}" type="button">'
                  f'{html.escape(PAISES.get(_p, _p))} <i>{_n}</i></button>')
FILTROS = '\n        '.join(_chips)

# Ciudades con pin, una sola vez cada una, y las ciudades que tiene cada pais.
_ciudades, _por_pais, _anios_de = [], {}, {}
for _a, _its in EXPOS:
    for _i in _its:
        _c, _p = ciudad_de(_i['lugar']), pais_de(_i['lugar'])
        if not _c: continue
        if _c not in [x[0] for x in _ciudades]:
            _ciudades.append((_c, _p))
        _por_pais.setdefault(_p, set()).add(_c)
        _anios_de.setdefault(_c, set()).add(_a)
_ciudades = [(c, p, _anios_de[c]) for c, p in _ciudades]

MAPA_TIERRA = mapa.mapa_svg()
MAPA_PINES  = mapa.pines_svg(_ciudades)

# A tamano de celular el mapa entero deja los puntos diminutos. Para cada anio
# se calcula el encuadre de sus ciudades y el dibujo se acerca ahi, que es lo
# unico que lo vuelve legible en una pantalla de mano.
_ENCUADRES = {}
for _a, _its in EXPOS:
    _cs = [ciudad_de(_i['lugar']) for _i in _its]
    _caja = mapa.caja_de([c for c in _cs if c])
    if not _caja:
        _ENCUADRES[_a] = [500, 215, 1.0]
        continue
    _x0, _y0, _x1, _y1 = _caja
    _m = 95                                    # aire alrededor de los pines
    _an, _al = (_x1 - _x0) + _m * 2, (_y1 - _y0) + _m * 2
    _z = min(1.35, max(1.0, min(1000.0 / _an, 430.0 / _al)))
    _ENCUADRES[_a] = [round((_x0 + _x1) / 2, 1), round((_y0 + _y1) / 2, 1), round(_z, 2)]
ENCUADRES = json.dumps(_ENCUADRES)

# Un mosaico por ciudad, definido una sola vez y referenciado por las tarjetas
# que lo necesiten. Veinticinco copias inline pesarian el doble de la pagina.
N_CIUDADES  = len(_ciudades)

_filas_pais = []
for _p, _cs in sorted(_por_pais.items(), key=lambda x: (-len(x[1]), x[0])):
    _n = len(_cs)
    _filas_pais.append(
      f'<li><button type="button" data-pais="{html.escape(_p)}">'
      f'<span class="punto" aria-hidden="true"></span>'
      f'<span class="nom">{html.escape(PAISES.get(_p, _p))}</span>'
      f'<span class="cuantas">{_n} {"city" if _n == 1 else "cities"}</span></button>'
      f'<span class="ciudades">{html.escape(", ".join(sorted(_cs)))}</span></li>')
PAISES_LISTA = '\n          '.join(_filas_pais)

# De lo mas reciente a lo mas viejo, igual que el registro de arriba. Al reves
# uno terminaba de leer 2021 y el mapa arrancaba otra vez en 2021 yendo hacia
# adelante: dos sentidos distintos en la misma pagina, y se perdia el hilo.
RIEL_ANIOS = ''.join(
  f'<button type="button" data-ir="{_a}"><i></i><span>{_a}</span></button>'
  for _a, _ in sorted(EXPOS, key=lambda x: x[0], reverse=True))

# Las que todavia no pasaron, de la mas cercana a la mas lejana.
_prox = [(a, i) for a, its in sorted(EXPOS, key=lambda x: x[0])
         for i in its if i.get('estado') == 'upcoming']
_rot = ['Next', 'Then', 'Later']
PROXIMAS = '\n        '.join(
  f'<article class="prox"><div class="eti">{_rot[min(n, 2)]} · {a}</div>'
  f'<h3>{html.escape(i["nombre"])}</h3>'
  f'<p>{html.escape(i["lugar"])}</p></article>'
  for n, (a, i) in enumerate(_prox))

CV_JS = """
<script>
/* El CV tiene dos momentos. Primero la escena del mapa: una seccion alta con
   un panel pegado, donde bajar hace avanzar los anios y encenderse las
   ciudades. Despues el catalogo, que es un documento y se filtra. */
(function(){
  var escena  = document.getElementById('escena');
  if(!escena) return;
  var pines   = document.querySelectorAll('.mundo-escena .pin'),
      rotulo  = document.getElementById('anio-grande'),
      donde   = document.getElementById('donde'),
      marcas  = document.querySelectorAll('.riel-anios button'),
      cuantas = document.getElementById('cuantas-anio'),
      chips   = document.querySelectorAll('.registro .filtros .chip'),
      filas   = document.querySelectorAll('.registro .fila'),
      anios   = document.querySelectorAll('.registro .cv .anio'),
      cuenta  = document.getElementById('cuenta-expos');
  var lista = [].map.call(marcas, function(b){ return b.getAttribute('data-ir'); });

  function ciudadesDe(anio){
    var cs = [];
    pines.forEach(function(p){
      if((p.getAttribute('data-anios')||'').split(' ').indexOf(anio) >= 0){
        var t = p.querySelector('text'); if(t) cs.push(t.textContent);
      }
    });
    return cs;
  }

  var ENCUADRES = {ENCUADRES};
  var camara = document.getElementById('camara');

  var actual = null;
  function verAnio(anio){
    if(anio === actual) return;
    actual = anio;
    /* El dibujo se acerca al encuadre del anio. Se mueve el grupo entero en
       vez del viewBox porque el viewBox no se puede animar con CSS. */
    if(camara && ENCUADRES[anio]){
      var e = ENCUADRES[anio];
      camara.style.transform =
        'translate(' + (500 - e[0] * e[2]) + 'px,' + (215 - e[1] * e[2]) + 'px) scale(' + e[2] + ')';
      camara.style.setProperty('--z', e[2]);
    }
    if(rotulo){
      rotulo.classList.add('cambia');
      setTimeout(function(){ rotulo.textContent = anio; rotulo.classList.remove('cambia'); }, 140);
    }
    var cs = ciudadesDe(anio);
    if(donde) donde.textContent = cs.length ? cs.join('  ·  ') : 'Online';
    if(cuantas){
      var n = document.querySelectorAll('.registro .cv .anio[data-anio="' + anio + '"] .fila').length;
      cuantas.textContent = n ? n + (n === 1 ? ' show' : ' shows and talks') : '';
    }
    pines.forEach(function(p){
      p.classList.toggle('activo', (p.getAttribute('data-anios')||'').split(' ').indexOf(anio) >= 0);
    });
    marcas.forEach(function(b){ b.classList.toggle('activo', b.getAttribute('data-ir') === anio); });
  }

  /* Cada ano se lleva una tajada igual del recorrido de la escena. */
  var pedido = 0;
  function mide(){
    if(!escena) return;
    escena.style.height = (window.innerHeight + lista.length * window.innerHeight * 0.34) + 'px';
    pinta();
  }
  function pinta(){
    if(!escena) return;
    var caja = escena.getBoundingClientRect();
    var total = escena.offsetHeight - window.innerHeight;
    var avance = total > 0 ? Math.min(.9999, Math.max(0, -caja.top / total)) : 0;
    verAnio(lista[Math.floor(avance * lista.length)]);
  }
  function alScroll(){
    if(pedido) return;
    pedido = requestAnimationFrame(function(){ pedido = 0; pinta(); });
  }
  addEventListener('scroll', alScroll, {passive:true});
  addEventListener('resize', mide);
  mide();

  /* Las marcas del riel llevan al tramo de ese ano. */
  marcas.forEach(function(b, n){
    b.addEventListener('click', function(){
      var total = escena.offsetHeight - window.innerHeight;
      var arriba = escena.offsetTop + total * ((n + .35) / lista.length);
      scrollTo({top: arriba, behavior:'smooth'});
    });
  });

  /* El catalogo, abajo, se filtra aparte. No toca el mapa. */
  function filtrar(pais, tipo, estado){
    var visibles = 0;
    filas.forEach(function(f){
      var ok = true;
      if(pais)        ok = f.getAttribute('data-pais') === pais;
      else if(tipo)   ok = f.getAttribute('data-tipo') === tipo;
      else if(estado) ok = f.getAttribute('data-estado') === estado;
      f.hidden = !ok;
      if(ok) visibles++;
    });
    anios.forEach(function(a){ a.hidden = !a.querySelector('.fila:not([hidden])'); });
    if(cuenta) cuenta.textContent = visibles;
  }
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      chips.forEach(function(o){ o.classList.toggle('activo', o === c); });
      filtrar(c.getAttribute('data-pais'), c.getAttribute('data-tipo'),
              c.getAttribute('data-filtro') === 'upcoming' ? 'upcoming' : null);
    });
  });
  pines.forEach(function(p){
    p.addEventListener('click', function(){
      var b = document.querySelector('.registro .filtros .chip[data-pais="' + p.getAttribute('data-pais') + '"]');
      if(b){ b.click(); b.scrollIntoView({behavior:'smooth', block:'center'}); }
    });
  });

  if('IntersectionObserver' in window){
    var ojo = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting){ e.target.classList.add('visible'); ojo.unobserve(e.target); }
      });
    }, {rootMargin:'0px 0px -6% 0px', threshold:0.06});
    document.querySelectorAll('.cv .anio, .prox, .resumen').forEach(function(n){
      n.classList.add('entra'); ojo.observe(n);
    });
  }
})();


/* Arrastrar los rieles con el mouse. Con dedo y con trackpad el navegador ya
   los desliza solo; con un mouse de rueda habria que saber el truco de la
   tecla shift, y nadie lo sabe. */
(function(){
  document.querySelectorAll('.registro .riel').forEach(function(riel){
    var abajo = false, movido = false, x0 = 0, izq0 = 0;

    riel.addEventListener('pointerdown', function(ev){
      if(ev.pointerType === 'touch') return;      // el dedo ya funciona solo
      abajo = true; movido = false;
      x0 = ev.clientX; izq0 = riel.scrollLeft;
      riel.setPointerCapture(ev.pointerId);
    });
    riel.addEventListener('pointermove', function(ev){
      if(!abajo) return;
      var d = ev.clientX - x0;
      if(Math.abs(d) > 4){ movido = true; riel.classList.add('agarrando'); }
      riel.scrollLeft = izq0 - d;
    });
    function soltar(ev){
      if(!abajo) return;
      abajo = false; riel.classList.remove('agarrando');
      try{ riel.releasePointerCapture(ev.pointerId); }catch(e){}
    }
    riel.addEventListener('pointerup', soltar);
    riel.addEventListener('pointercancel', soltar);
    /* Si se arrastro, el clic que viene despues no debe abrir la lupa. */
    riel.addEventListener('click', function(ev){
      if(movido){ ev.preventDefault(); ev.stopPropagation(); movido = false; }
    }, true);
  });
})();

/* El riel de cada ano avanza un poco solo al bajar, sin estirar el bloque.

   Antes se le ponia al ano una altura minima enorme para tener pista de
   scroll, y como el contenido no la llenaba quedaban huecos negros de media
   pantalla entre el ano y sus fotos. Ahora el riel se mueve con el viaje
   natural del bloque por la pantalla: da vida y no rompe nada. Lo que falte,
   se arrastra con la mano. */
(function(){
  var rieles = document.querySelectorAll('.registro .riel');
  if(!rieles.length) return;

  var piezas = [];
  rieles.forEach(function(riel){
    var p = {riel:riel, bloque:riel.closest('.anio'), sobra:0, suelto:false, destino:null};

    /* Antes bastaba con posar el dedo para que el riel se soltara: al bajar la
       pagina, el primer toque caia encima de una foto y el avance automatico
       se apagaba para siempre. Y si uno intentaba deslizar mientras el riel se
       movia solo, los dos tiraban al tiempo y se sentia trabado.
       Ahora solo se suelta ante un gesto claramente horizontal, y el avance se
       corta en seco, sin forcejeo. */
    var x0 = 0, y0 = 0, mirando = false;
    function empieza(x, y){ x0 = x; y0 = y; mirando = true; }
    function mueve(x, y){
      if(!mirando || p.suelto) return;
      var dx = Math.abs(x - x0), dy = Math.abs(y - y0);
      if(dx > 10 && dx > dy * 1.4){ p.suelto = true; p.destino = null; }
      else if(dy > 14){ mirando = false; }
    }
    riel.addEventListener('pointerdown', function(e){ empieza(e.clientX, e.clientY); });
    riel.addEventListener('pointermove', function(e){ mueve(e.clientX, e.clientY); });
    riel.addEventListener('pointerup', function(){ mirando = false; });
    riel.addEventListener('touchstart', function(e){
      empieza(e.touches[0].clientX, e.touches[0].clientY); }, {passive:true});
    riel.addEventListener('touchmove', function(e){
      mueve(e.touches[0].clientX, e.touches[0].clientY); }, {passive:true});
    riel.addEventListener('touchend', function(){ mirando = false; }, {passive:true});
    /* La rueda horizontal del trackpad tambien es intencion de la persona. */
    riel.addEventListener('wheel', function(e){
      if(Math.abs(e.deltaX) > Math.abs(e.deltaY)){ p.suelto = true; p.destino = null; }
    }, {passive:true});

    piezas.push(p);
  });

  function mide(){
    piezas.forEach(function(p){
      p.sobra = Math.max(0, p.riel.scrollWidth - p.riel.clientWidth);
    });
    pinta();
  }

  var pedido = 0, corazon = 0;
  function pinta(){
    var alto = window.innerHeight;
    piezas.forEach(function(p){
      if(p.suelto || p.sobra < 24) return;
      /* El avance se mide sobre el riel, no sobre el bloque entero, y solo
         mientras esta a la vista. Antes iba de que el bloque entraba por abajo
         a que salia por arriba: para cuando uno lo tenia centrado leyendo, el
         movimiento ya casi habia terminado y parecia que las fotos no se
         movian. */
      var c = p.riel.getBoundingClientRect();
      var arranca = alto * .88, termina = -c.height * .35;
      if(c.top > arranca || c.top < termina - 40) return;
      var avance = Math.min(1, Math.max(0, (arranca - c.top) / (arranca - termina)));
      var suave = avance < .5 ? 2 * avance * avance
                              : 1 - Math.pow(-2 * avance + 2, 2) / 2;
      p.destino = suave * p.sobra;
    });
  }
  function late(){
    var vivo = false;
    piezas.forEach(function(p){
      if(p.suelto || p.destino == null) return;
      var d = p.destino - p.riel.scrollLeft;
      if(Math.abs(d) < .5) return;
      p.riel.scrollLeft += d * 0.1;
      vivo = true;
    });
    corazon = vivo ? requestAnimationFrame(late) : 0;
  }
  function alScroll(){
    if(!pedido) pedido = requestAnimationFrame(function(){ pedido = 0; pinta(); });
    if(!corazon) corazon = requestAnimationFrame(late);
  }

  addEventListener('scroll', alScroll, {passive:true});
  addEventListener('resize', mide);
  document.querySelectorAll('.registro .riel img').forEach(function(im){
    if(!im.complete) im.addEventListener('load', mide, {once:true});
  });
  mide();
})();
</script>
"""




cv = cabeza(
  'CV · JUDASACA · Juan Salazar',
  'Exhibition history of JUDASACA, 2021 to 2027: New York, Miami, Los Angeles, '
  'Tokyo, Lisbon, Barcelona, Mexico City, Costa Rica, Lima and Bogotá.',
  'cv.html') + f'''
<main>
  <section>
    <div class="wrap">
      <div class="tit">
        <div class="eti">Curriculum</div>
        <h2>Exhibitions</h2>
        <p>Juan Salazar · JUDASACA · born and based in Bogotá, Colombia.
          {N_MUESTRAS} exhibitions across {N_PAISES} countries since {ANIO_0},
          from Bogotá to New York, Tokyo and Lisbon.</p>
      </div>

      <div class="proximas">
        {PROXIMAS}
      </div>

      <div class="hitos">
        {DESTACADOS}
      </div>

      <div class="resumen">
        <div><b>{N_MUESTRAS}</b><span>Exhibitions</span></div>
        <div><b>{N_PAISES}</b><span>Countries</span></div>
        <div><b>{N_CIUDADES}</b><span>Cities</span></div>
        <div><b>{ANIO_0}</b><span>Since</span></div>
      </div>
    </div>
  </section>

  <section class="viaje registro">
    <div class="wrap catalogo">
      <div class="cat-cab">
        <div>
          <div class="eti">Full record</div>
          <h2>Every show and talk, newest first</h2>
        </div>
        <p class="contados"><b id="cuenta-expos">{N_EXPOS}</b> of {N_EXPOS} shown</p>
      </div>

      <details class="filtro-caja">
        <summary><span>Filter</span><i aria-hidden="true"></i></summary>
        <div class="filtros" role="group" aria-label="Filter exhibitions">
          {FILTROS}
        </div>
      </details>

      <div class="cv">
{chr(10).join(bloque_anio(a, its) for a, its in EXPOS)}
      </div>
    </div>
  </section>
  <section class="viaje mundo-escena" id="viaje">
    <div class="escena" id="escena">
      <div class="escena-pega">
        <div class="mapa-fondo">
            <svg viewBox="0 0 1000 430" role="img"
                 aria-label="World map with the cities where JUDASACA has exhibited">
              <g id="camara" class="camara">
                <g class="tierra">{MAPA_TIERRA}</g>
                {MAPA_PINES}
              </g>
            </svg>
        </div>

        <div class="wrap escena-txt">
          <div class="eti">The road so far</div>
          <div class="anio-grande" id="anio-grande">{ANIO_FIN}</div>
          <div class="donde" id="donde">&nbsp;</div>
          <div class="cuantas-anio" id="cuantas-anio">&nbsp;</div>
          <div class="riel-anios" id="riel-anios">{RIEL_ANIOS}</div>
        </div>
      </div>
    </div>
  </section>

  <section>
    <div class="wrap" style="text-align:center">
      <p style="margin-top:8px"><a class="btn" href="contact.html">Request full dossier</a></p>
    </div>
  </section>
</main>
''' + CV_JS.replace('{ENCUADRES}', ENCUADRES) + PIE

# ══════════════════════════════════════════════════════════════════════════
# 6 · CONTACT
# ══════════════════════════════════════════════════════════════════════════
contact = cabeza(
  'Contact · JUDASACA',
  'Contact Juan Salazar, JUDASACA. Bogotá, Colombia. Enquiries about original '
  'works, exhibitions and commissions.',
  'contact.html', og='img/nothing-stays-the-same-sm.webp') + f'''
<main>
  <section>
    <div class="wrap estrecho contacto">
      <!-- Una obra y no un retrato: la pagina de contacto es el ultimo sitio donde
           alguien duda, y lo que tiene que ver ahi es el trabajo. -->
      <figure class="obra-contacto">
        <img src="contact_photo.webp" alt="Juan Salazar with a signed print of Smiling Ratsquiat, King Crown">
        <figcaption><span class="t1">Smiling Ratsquiat,</span> <span class="t2">King Crown</span></figcaption>
      </figure>

      <div class="tit">
        <div class="eti">Contact</div>
        <h2>Say something</h2>
        <p>Enquiries about available works, exhibitions, commissions and collaborations
          all reach the same place, and Juan answers them himself.</p>
      </div>

      <form class="forma" id="forma" action="https://api.web3forms.com/submit" method="POST">
        <input type="hidden" name="access_key" value="{LLAVE_FORM}">
        <input type="hidden" name="subject" value="New enquiry from judasaca.art">
        <input type="hidden" name="from_name" value="judasaca.art">
        <!-- Trampa para robots: un humano nunca la ve ni la llena. Si viene
             marcada, Web3Forms descarta el envio sin molestar a nadie. -->
        <input type="checkbox" name="botcheck" class="miel" tabindex="-1" autocomplete="off">

        <div class="dos-campos">
          <div class="campo">
            <label for="nombre">First name</label>
            <input id="nombre" name="First name" type="text" required autocomplete="given-name">
          </div>
          <div class="campo">
            <label for="apellido">Last name</label>
            <input id="apellido" name="Last name" type="text" autocomplete="family-name">
          </div>
        </div>
        <div class="campo">
          <label for="correo">Email</label>
          <input id="correo" name="email" type="email" required autocomplete="email">
        </div>
        <div class="campo">
          <label for="mensaje">Message</label>
          <textarea id="mensaje" name="Message" rows="5" required></textarea>
        </div>
        <button class="btn lleno enviar" type="submit">Send</button>
        <p class="aviso-forma" id="aviso-forma" role="status" aria-live="polite"></p>
      </form>

      <p class="o-bien">Or write directly to
        <a class="correo-linea" href="mailto:{CORREO}">{CORREO}</a></p>

      <div class="enlaces">
        <a href="{IG}" rel="noopener">Instagram · @judasaca</a>
        <a href="art.html">Available works</a>
        <a href="cv.html">CV</a>
      </div>

      <div class="prosa" style="margin-top:48px">
        <h3>Based in Bogotá</h3>
        <p>Works ship worldwide. For exhibitions and press, ask for the full dossier and
          high-resolution images and they will be sent the same day.</p>
      </div>
    </div>
  </section>
</main>

<script>
/* Envia sin recargar la pagina. Si el JavaScript falla o esta apagado, el form
   se manda igual por POST normal: Web3Forms responde con su propia pagina de
   gracias. Nunca queda un formulario que no hace nada. */
(function(){{
  var f=document.getElementById('forma'); if(!f||!window.fetch) return;
  var aviso=document.getElementById('aviso-forma'), boton=f.querySelector('button');
  f.addEventListener('submit', function(e){{
    e.preventDefault();
    aviso.className='aviso-forma'; aviso.textContent='Sending…'; boton.disabled=true;
    fetch(f.action, {{method:'POST', body:new FormData(f), headers:{{'Accept':'application/json'}}}})
      .then(function(r){{ return r.json(); }})
      .then(function(d){{
        if(!d.success) throw new Error(d.message||'error');
        f.reset();
        aviso.className='aviso-forma ok';
        aviso.textContent='Thank you. Juan reads these himself and will reply from {CORREO}.';
      }})
      .catch(function(){{
        aviso.className='aviso-forma mal';
        aviso.textContent='That did not go through. Please write directly to {CORREO}.';
      }})
      .then(function(){{ boton.disabled=false; }});
  }});
}})();
</script>
''' + PIE

# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
# 7 · PRIVACIDAD
# ══════════════════════════════════════════════════════════════════════════
# No va en el menu principal: nadie entra a una web de arte buscando la
# politica de privacidad. Va en el pie, que es donde se busca cuando se busca.
privacidad = cabeza(
  'Privacy · JUDASACA',
  'How judasaca.art handles personal data: the contact form, payments through '
  'Bold, and your rights under Colombian law.',
  'privacy.html') + f'''
<main>
  <section>
    <div class="wrap estrecho">
      <div class="tit">
        <div class="eti">Privacy</div>
        <h2>What we collect, and what we do not</h2>
        <p>Short version: a name, an email and a message if you write to us. Nothing else,
          and never a card number.</p>
      </div>

      <div class="prosa">
        <h3>Who is responsible</h3>
        <p>Juan Salazar, working as JUDASACA, in Bogotá, Colombia.
          Questions about anything on this page go to
          <a href="mailto:{CORREO}">{CORREO}</a>.</p>

        <h3>What this site collects</h3>
        <p><b>The contact form.</b> Your first name, last name, email address and the
          message you write. We use them to answer you and for nothing else. They are not
          sold, rented or shared, and there is no mailing list to be added to.</p>
        <p><b>The selection of works.</b> When you add a piece to the selection, that list
          is saved in your own browser and never leaves your device. It is not a cookie and
          it is not sent to us. Clearing your browser data erases it.</p>
        <p><b>Payments.</b> Card details are entered inside Bold's payment gateway. They do
          not pass through this site and we never see, receive or store them.</p>

        <h3>Who else touches this information</h3>
        <table class="tabla-privacidad">
          <tr><td><b>Web3Forms</b></td><td>Delivers the contact form to our inbox.</td></tr>
          <tr><td><b>Bold</b></td><td>Processes payments. Colombian payment gateway.</td></tr>
          <tr><td><b>Cloudflare</b></td><td>Signs each sale so its amount cannot be altered.
            It receives only which artwork was chosen, never who you are.</td></tr>
        </table>

        <h3>Your rights</h3>
        <p>Under Ley 1581 de 2012 you may ask us what data we hold about you, correct it,
          update it, or ask us to delete it, and you may withdraw your permission at any
          time. Write to <a href="mailto:{CORREO}">{CORREO}</a> and Juan answers himself.
          Consultations are answered within ten working days and complaints within fifteen.</p>

        <h3>Cookies</h3>
        <p>This site sets no advertising or tracking cookies, and there is nothing here
          following you to other websites.</p>

        <h3>Encryption</h3>
        <p>The whole site is served over HTTPS, so everything travelling between your
          browser and this site is encrypted, including whatever you type into the contact
          form. Payment encryption is handled inside Bold's gateway.</p>

        <p class="chico">Last updated <span class="dato-fecha">August 2026</span>.</p>
      </div>
    </div>
  </section>
</main>
''' + PIE


# ══════════════════════════════════════════════════════════════════════════
# 8 · DESPUES DEL PAGO
# ══════════════════════════════════════════════════════════════════════════
# Bold devuelve al comprador aqui con ?bold-order-id=...&bold-tx-status=...
# El estado que llega en la URL es informativo y puede no ser el definitivo, asi
# que el texto no promete nada que no se pueda sostener: dice lo que Bold dijo y
# remite a Juan, que es quien confirma de verdad.
gracias = cabeza(
  'Thank you · JUDASACA',
  'Payment confirmation for your order at judasaca.art.',
  'thanks.html') + f'''
<main>
  <section>
    <div class="wrap estrecho prosa gracias">
      <div class="tit centrado">
        <div class="eti">Order</div>
        <h2 id="titulo-gracias">Thank you</h2>
      </div>
      <p id="mensaje-gracias" style="text-align:center">Juan will write to you from {CORREO} to
        confirm the work and arrange shipping to your city.</p>
      <p class="chico" id="referencia-gracias" style="color:var(--tenue);text-align:center"></p>

      <!-- La direccion se pide AQUI y no antes de pagar. Antes del pago cada
           campo es una excusa para no comprar; despues del pago el comprador ya
           esta contento y quiere que le llegue el cuadro. -->
      <div id="caja-envio" hidden>
        <h3 style="margin-top:38px">Where should it go?</h3>
        <p>Juan ships worldwide. Leave the address and he confirms the cost and the
          date the same day.</p>
        <form class="forma" id="form-envio">
          <div class="campo">
            <label for="e-nombre">Full name</label>
            <input id="e-nombre" name="nombre" type="text" required autocomplete="name">
          </div>
          <div class="dos-campos">
            <div class="campo">
              <label for="e-email">Email</label>
              <input id="e-email" name="email" type="email" required autocomplete="email">
            </div>
            <div class="campo">
              <label for="e-telefono">Phone</label>
              <input id="e-telefono" name="telefono" type="tel" required autocomplete="tel">
            </div>
          </div>
          <div class="campo">
            <label for="e-direccion">Address</label>
            <input id="e-direccion" name="direccion" type="text" required autocomplete="street-address">
          </div>
          <div class="dos-campos">
            <div class="campo">
              <label for="e-ciudad">City</label>
              <input id="e-ciudad" name="ciudad" type="text" required autocomplete="address-level2">
            </div>
            <div class="campo">
              <label for="e-pais">Country</label>
              <input id="e-pais" name="pais" type="text" required autocomplete="country-name">
            </div>
          </div>
          <div class="campo">
            <label for="e-notas">Anything Juan should know</label>
            <input id="e-notas" name="notas" type="text" autocomplete="off">
          </div>
          <button class="btn lleno enviar" type="submit">Send shipping details</button>
          <p class="aviso-forma" id="aviso-envio" role="status" aria-live="polite"></p>
        </form>
      </div>

      <p style="margin-top:34px;text-align:center"><a class="btn" href="art.html">Back to the works</a></p>
    </div>
  </section>
</main>

<script>
(function(){{
  var p = new URLSearchParams(window.location.search);
  var estado = (p.get('bold-tx-status') || '').toLowerCase();
  var orden = p.get('bold-order-id');
  var t = document.getElementById('titulo-gracias');
  var m = document.getElementById('mensaje-gracias');
  var r = document.getElementById('referencia-gracias');
  var caja = document.getElementById('caja-envio');

  // Respaldo: si Bold no devolviera la referencia en la URL, se recupera la que
  // el sitio guardo justo antes de abrir la pasarela.
  var guardada = null;
  try {{ guardada = JSON.parse(localStorage.getItem('judasaca-orden') || 'null'); }} catch(e) {{}}
  if (!orden && guardada && guardada.id) orden = guardada.id;

  var aprobada = (estado === 'approved');

  if (aprobada) {{
    t.textContent = 'Thank you';
    m.textContent = 'Your payment went through. One last thing and it is done.';
  }} else if (estado === 'rejected' || estado === 'failed') {{
    t.textContent = 'That payment did not go through';
    m.textContent = 'Nothing has been charged. You can try again, or write to {CORREO} '
      + 'and Juan will sort it out with you directly.';
  }} else if (estado) {{
    t.textContent = 'Your payment is being processed';
    m.textContent = 'Bold has not confirmed it yet. As soon as it settles, Juan will write '
      + 'to you from {CORREO}.';
  }}
  if (orden) r.textContent = 'Reference: ' + orden;

  /* El webhook de Bold puede tardar hasta diez minutos. El comprador esta aqui
     ahora. Se le avisa al Worker para que marque la obra enseguida; el Worker
     no se fia de esto y lo verifica contra Bold antes de hacer nada. */
  if (orden && aprobada && window.fetch) {{
    fetch('{FIRMADOR}/confirmar', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ orderId: orden }})
    }}).catch(function(){{ }});

    // Lo pagado sale del carrito. Si no, sigue ahi tentando a pagarlo otra vez.
    try {{
      var comprados = (guardada && guardada.slugs) || [];
      var carro = JSON.parse(localStorage.getItem('judasaca-carro') || '[]');
      localStorage.setItem('judasaca-carro', JSON.stringify(
        carro.filter(function(s){{ return comprados.indexOf(s) < 0; }})));
    }} catch(e) {{}}
  }}

  if (!aprobada || !orden) return;
  caja.hidden = false;

  var f = document.getElementById('form-envio');
  var aviso = document.getElementById('aviso-envio');
  f.addEventListener('submit', function(e){{
    e.preventDefault();
    var boton = f.querySelector('button[type=submit]');
    boton.disabled = true;
    aviso.className = 'aviso-forma';
    aviso.textContent = 'Sending…';

    var datos = {{ orderId: orden }};
    ['nombre','email','telefono','direccion','ciudad','pais','notas']
      .forEach(function(k){{ datos[k] = (f[k] && f[k].value || '').trim(); }});

    fetch('{FIRMADOR}/datos', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(datos)
    }})
    .then(function(rr){{ return rr.json(); }})
    .then(function(d){{
      if (!d || !d.ok) throw new Error('no');
      f.innerHTML = '';
      aviso.className = 'aviso-forma ok';
      aviso.textContent = 'Got it. Juan has your address and will write from {CORREO} '
        + 'with the shipping date.';
      f.appendChild(aviso);
    }})
    .catch(function(){{
      boton.disabled = false;
      aviso.className = 'aviso-forma mal';
      aviso.textContent = 'That did not save. Please send your address to {CORREO} '
        + 'quoting the reference above.';
    }});
  }});
}})();
</script>
''' + PIE


if __name__ == '__main__':
    for nombre, cuerpo in [('index.html', home), ('about.html', about), ('art.html', art),
                           ('shop.html', shop), ('cv.html', cv), ('contact.html', contact),
                           ('privacy.html', privacidad), ('thanks.html', gracias)]:
        n = escribir(nombre, cuerpo)
        print(f'  {nombre:<14} {n/1024:>6.1f} KB')

    # CNAME para GitHub Pages, robots y sitemap
    escribir('CNAME', 'judasaca.art\n')
    escribir('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n')
    # lastmod le dice a Google que cambio y cuando. Sin esto tiene que
    # adivinar cada cuanto volver a pasar, y con un sitio pequeno que no
    # visita casi nadie, adivina "casi nunca". Se saca de la fecha real del
    # archivo recien escrito, asi que no hay que acordarse de tocarla.
    hoy = __import__('datetime').date.today().isoformat()
    urls = ''.join(
        f'  <url><loc>{SITIO}/{"" if a == "index.html" else a}</loc>'
        f'<lastmod>{hoy}</lastmod>'
        f'<priority>{"1.0" if a == "index.html" else "0.8"}</priority></url>\n'
        # privacy.html no esta en PAGINAS porque no va en el menu, pero si debe
        # poder indexarse: es la pagina que alguien busca cuando desconfia.
        for a, _ in PAGINAS + [('privacy.html', 'Privacy')])
    escribir('sitemap.xml',
             f'<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    print('\n  CNAME · robots.txt · sitemap.xml')
    print(f'  {len(OBRAS)} obras · {len(TIENDA)} en tienda mas las medias · '
          f'{sum(len(i) for _, i in EXPOS)} exposiciones')
