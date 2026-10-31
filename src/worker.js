// Una sola dirección para cada página: https://downtownlifevipmargarita.com/...
// Redirige (301 permanente) cualquier visita por http:// o por www. a esa versión,
// para que Google no vea páginas duplicadas. El resto se sirve desde dist/.
const HOST = "downtownlifevipmargarita.com";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const isWww = url.hostname === "www." + HOST;
    if (url.protocol === "http:" || isWww) {
      url.protocol = "https:";
      if (isWww) url.hostname = HOST;
      return Response.redirect(url.toString(), 301);
    }
    return env.ASSETS.fetch(request);
  },
};
