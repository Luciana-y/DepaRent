// Revelado al entrar en pantalla, una sola vez. Los estados ocultos solo existen en CSS bajo
// `.js` y `prefers-reduced-motion: no-preference`; si el observador no existe, todo queda visible.
export function activarMovimiento(raiz = document) {
  const elementos = [...raiz.querySelectorAll("[data-reveal]:not(.is-in)")];
  if (!elementos.length) return;
  if (!("IntersectionObserver" in window)) {
    elementos.forEach((el) => el.classList.add("is-in"));
    return;
  }
  const observador = new IntersectionObserver((entradas) => {
    for (const entrada of entradas) {
      if (!entrada.isIntersecting) continue;
      entrada.target.classList.add("is-in");
      observador.unobserve(entrada.target);
    }
  }, { rootMargin: "0px 0px -12% 0px", threshold: 0.1 });
  elementos.forEach((el) => observador.observe(el));
}
