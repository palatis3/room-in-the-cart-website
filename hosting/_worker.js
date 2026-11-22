const canonicalHost = "roominthecart.com";
const robots = "noindex, follow";
const helpPaths = new Map([
  ["/privacy", "/privacy"],
  ["/support", "/support"],
  ["/es/privacidad", "/privacy"],
  ["/es/soporte", "/support"],
]);

function helpDestination(url) {
  const path = url.pathname.replace(/\/$/, "");
  const document = helpPaths.get(path);
  if (!document) return;
  const target = new URL(document, "https://help.roominthecart.com");
  const language = url.searchParams.get("lang")?.toLowerCase();
  if (path.startsWith("/es/") || language === "es" || language === "es-mx") {
    target.searchParams.set("lang", "es");
    target.hash = "es";
  } else if (language === "en" || language === "en-us") {
    target.searchParams.set("lang", "en");
  }
  return target;
}

function redirectToCanonical(url) {
  url.protocol = "https:";
  url.host = canonicalHost;
  return new Response(null, {
    status: 308,
    headers: { Location: url.href, "X-Robots-Tag": robots },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "www." + canonicalHost ||
        (url.hostname === canonicalHost && url.protocol === "http:")) {
      return redirectToCanonical(url);
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", {
        status: 405,
        headers: { Allow: "GET, HEAD", "X-Robots-Tag": robots },
      });
    }
    const help = helpDestination(url);
    if (help) {
      return new Response(null, {
        status: 308,
        headers: { Location: help.href, "X-Robots-Tag": robots },
      });
    }
    const asset = await env.ASSETS.fetch(request);
    const headers = new Headers(asset.headers);
    headers.set("X-Robots-Tag", robots);
    return new Response(asset.body, {
      status: asset.status,
      statusText: asset.statusText,
      headers,
    });
  },
};
