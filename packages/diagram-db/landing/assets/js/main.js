/* diagram-db — landing/main.js
   Navegación, revelado al hacer scroll, botones de copia y pestañas.
   Sin dependencias: todo lo que hace falta son unas pocas APIs del navegador. */
(() => {
  "use strict";

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ============ Navegación móvil ============ */

  const navToggle = $(".nav-toggle");
  const navLinks = $("#nav-links");
  const smallScreen = window.matchMedia("(max-width: 48rem)");

  if (navToggle && navLinks) {
    const setOpen = (open) => {
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute(
        "aria-label",
        open ? "Cerrar menú de navegación" : "Abrir menú de navegación",
      );
      navLinks.hidden = smallScreen.matches ? !open : false;
    };

    const sync = () =>
      setOpen(smallScreen.matches ? navToggle.getAttribute("aria-expanded") === "true" : false);

    navToggle.addEventListener("click", () =>
      setOpen(navToggle.getAttribute("aria-expanded") !== "true"),
    );

    navLinks.addEventListener("click", (event) => {
      if (event.target.closest("a") && smallScreen.matches) setOpen(false);
    });

    smallScreen.addEventListener("change", () => {
      navToggle.setAttribute("aria-expanded", "false");
      sync();
    });

    sync();
  }

  /* ============ Revelado progresivo ============ */

  const revealables = $$(".reveal");

  if (!("IntersectionObserver" in window) || reducedMotion.matches) {
    revealables.forEach((element) => element.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 },
    );
    revealables.forEach((element) => observer.observe(element));
  }

  /* ============ Copiar al portapapeles ============ */

  const copyText = async (text) => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    const helper = document.createElement("textarea");
    helper.value = text;
    helper.setAttribute("readonly", "");
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.appendChild(helper);
    helper.select();
    const copied = document.execCommand("copy");
    helper.remove();
    return copied;
  };

  $$(".copy-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = $(button.dataset.copyTarget);
      if (!target) return;
      const text = target.textContent.trim();
      try {
        if (!(await copyText(text))) return;
        button.classList.add("is-copied");
        const original = button.getAttribute("aria-label");
        button.setAttribute("aria-label", "Copiado");
        window.setTimeout(() => {
          button.classList.remove("is-copied");
          if (original) button.setAttribute("aria-label", original);
        }, 1600);
      } catch {
        /* Sin permiso de portapapeles: el texto sigue seleccionable a mano. */
      }
    });
  });

  /* ============ Pestañas ============ */

  $$('[role="tablist"]').forEach((tablist) => {
    const tabs = $$('[role="tab"]', tablist);

    const select = (tab, focus = true) => {
      tabs.forEach((item) => {
        const active = item === tab;
        item.setAttribute("aria-selected", String(active));
        item.tabIndex = active ? 0 : -1;
        const panel = document.getElementById(item.getAttribute("aria-controls"));
        if (panel) panel.hidden = !active;
      });
      if (focus) tab.focus();
    };

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => select(tab, false));
      tab.addEventListener("keydown", (event) => {
        const index = tabs.indexOf(tab);
        let next = null;
        if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === "Home") next = tabs[0];
        if (event.key === "End") next = tabs[tabs.length - 1];
        if (!next) return;
        event.preventDefault();
        select(next);
      });
    });
  });
})();
