export default {
  async fetch(request, env) {
    const auth = request.headers.get("Authorization");

    if (auth) {
      const [scheme, encoded] = auth.split(" ");
      if (scheme === "Basic" && encoded) {
        const decoded = atob(encoded);
        const idx = decoded.indexOf(":");
        const user = decoded.slice(0, idx);
        const pass = decoded.slice(idx + 1);
        if (user === env.GATE_USER && pass === env.GATE_PASS) {
          const init = {
            method: request.method,
            headers: request.headers,
          };
          if (!["GET", "HEAD"].includes(request.method)) {
            init.body = await request.arrayBuffer();
          }
          return fetch(request.url, init);
        }
      }
    }

    return new Response("Authentication required.", {
      status: 401,
      headers: {
        "WWW-Authenticate": `Basic realm="${env.REALM || "Restricted"}", charset="UTF-8"`,
      },
    });
  },
};
