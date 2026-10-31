// Redirige cualquier visita por http:// a https:// (301 permanente),
// para que Google solo indexe la versión segura de cada página.
// El resto de peticiones se sirven tal cual desde la carpeta dist/.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.protocol === "http:") {
      url.protocol = "https:";
      return Response.redirect(url.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
