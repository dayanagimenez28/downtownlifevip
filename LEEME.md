# Web de Downtown Life VIP

## Qué hay en esta carpeta

- `dist/`: la web terminada, lista para subir a un hosting. Es lo único que necesita el hosting.
- `content/posts/`: los artículos del blog, uno por archivo `.md`.
- `fotos/`: las fotos de la web, optimizadas.
- `assets/`: diseño (CSS), tipografías y el pequeño script del menú y la galería.
- `build.py`: el generador que convierte los artículos y las páginas en la web de `dist/`.

## Publicar la web (gratis)

### Opción A: Netlify (la más sencilla)
1. Entra en https://app.netlify.com/drop.
2. Arrastra la carpeta `dist` a la página.
3. En unos segundos tendrás la web online con una dirección de prueba.
4. Crea una cuenta gratuita para guardarla y conectar tu dominio en *Domain management*.

### Opción B: Cloudflare Pages
1. Crea una cuenta en Cloudflare y entra en *Workers & Pages → Create → Pages → Upload assets*.
2. Sube la carpeta `dist`.
3. Conecta tu dominio en *Custom domains*.

## Cuando compres el dominio

1. Abre `build.py` y cambia la línea `"url": "https://downtownlifevipmargarita.com"` por tu dominio real si algún día cambia.
2. Si quieres, rellena también `whatsapp`, `instagram` y `email` en esa misma sección.
3. Vuelve a generar la web y súbela de nuevo.
4. Da de alta la web en Google Search Console (https://search.google.com/search-console) y envía el mapa del sitio: `https://TU-DOMINIO/sitemap.xml`.

## Publicar un artículo nuevo cada semana

1. Copia `content/posts/_plantilla.md` y cámbiale el nombre, por ejemplo `playa-el-agua-como-llegar.md`.
2. Rellena título, descripción, categoría, fecha y foto de portada, y escribe el texto.
3. Genera la web: `python3 build.py` (necesita Python 3 y `pip install markdown`).
4. Sube otra vez la carpeta `dist` a Netlify o Cloudflare.

O, más fácil: pídele a Claude el artículo de la semana y él te devuelve la web ya generada.

El generador crea automáticamente la página del artículo, lo añade al blog, a su categoría, a la portada, al mapa del sitio (`sitemap.xml`) y al feed (`feed.xml`).
