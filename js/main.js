/* RenoBeam — main.js
   Nav state, mobile menu, scroll-reveal via IntersectionObserver.
   Respects prefers-reduced-motion. No dependencies. */

(function () {
  "use strict";

  var docEl = document.documentElement;
  docEl.classList.add("has-js");

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------------- Sticky nav scrolled state ---------------- */

  var nav = document.querySelector(".nav");

  function onScroll() {
    if (!nav) return;
    nav.classList.toggle("scrolled", window.scrollY > 8);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------------- Mobile menu ---------------- */

  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("nav-links");

  function closeMenu() {
    if (!toggle || !links) return;
    toggle.setAttribute("aria-expanded", "false");
    links.classList.remove("open");
  }

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      links.classList.toggle("open", !open);
    });

    links.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeMenu();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }

  /* ---------------- Scroll reveal ---------------- */

  var revealEls = Array.prototype.slice.call(
    document.querySelectorAll("[data-reveal]")
  );

  function revealAll() {
    revealEls.forEach(function (el) {
      el.classList.add("revealed");
    });
  }

  if (reducedMotion.matches || !("IntersectionObserver" in window)) {
    revealAll();
  } else {
    /* Stagger siblings inside a reveal group */
    document.querySelectorAll("[data-reveal-group]").forEach(function (group) {
      Array.prototype.forEach.call(
        group.querySelectorAll("[data-reveal]"),
        function (el, i) {
          el.style.transitionDelay = Math.min(i * 80, 480) + "ms";
        }
      );
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    revealEls.forEach(function (el) {
      observer.observe(el);
    });

    /* If the user flips reduced-motion on mid-session, show everything */
    var onMotionChange = function (e) {
      if (e.matches) revealAll();
    };
    if (typeof reducedMotion.addEventListener === "function") {
      reducedMotion.addEventListener("change", onMotionChange);
    }
  }
})();
