import { useLayoutEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function sectionScrollTop(target, navHeight, scrollY, maxScroll) {
  if (target.id === "hero") return 0;
  return Math.max(0, Math.min(maxScroll, target.getBoundingClientRect().top + scrollY - navHeight));
}

export default function usePageMotion(containerRef, currentPath) {
  useLayoutEffect(() => {
    const root = containerRef.current;
    if (!root) return undefined;

    let disposed = false;
    let frame = 0;
    let settlingFrame = 0;
    let pendingHash = window.location.hash;
    const media = gsap.matchMedia();
    const nav = root.querySelector(".top-nav, header");
    const previousOffset = root.style.getPropertyValue("--site-nav-offset");
    const navbarHeight = () => nav?.getBoundingClientRect().height || 0;

    function alignHash() {
      if (!pendingHash) return;
      let id;
      try {
        id = decodeURIComponent(pendingHash.slice(1));
      } catch {
        return;
      }
      const target = document.getElementById(id);
      if (!target || !root.contains(target)) return;
      window.scrollTo({
        top: sectionScrollTop(target, navbarHeight(), window.scrollY, ScrollTrigger.maxScroll(window)),
        behavior: "instant",
      });
    }

    function refreshLayout() {
      if (disposed) return;
      root.style.setProperty("--site-nav-offset", `${navbarHeight()}px`);
      // Measure the settled document before choosing the anchor destination.
      ScrollTrigger.refresh();
      alignHash();
      // Let scrub interpolate naturally, including after programmatic scrolling.
      // Forcing tween.progress(1) here would skip the visible movement.
      ScrollTrigger.update();
    }

    function scheduleRefresh() {
      if (disposed) return;
      cancelAnimationFrame(frame);
      cancelAnimationFrame(settlingFrame);
      frame = requestAnimationFrame(() => {
        refreshLayout();
        // Layout, fragment restoration and image sizing may settle a frame later.
        settlingFrame = requestAnimationFrame(refreshLayout);
      });
    }

    const context = gsap.context(() => {
      gsap.set(root, {
        backgroundImage: `url(${import.meta.env.BASE_URL}images/Tramonto.webp)`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
      });

      media.add("(prefers-reduced-motion: no-preference)", () => {
        if (currentPath !== "/") return undefined;
        // Animate top-level nav children only: no nested transforms on its links.
        const intro = gsap.utils.toArray(".top-nav > *, .hero-content > *", root);
        gsap.fromTo(intro, { y: 40, opacity: 0, scale: 0.96 }, {
          y: 0, opacity: 1, scale: 1, duration: 1.2, ease: "power2.out", stagger: 0.12,
        });

        root.querySelectorAll(".content-section").forEach((section) => {
          Array.from(section.children).forEach((element) => {
            gsap.fromTo(element, {
              y: 80, opacity: 0, scale: 0.96,
            }, {
              y: 0, opacity: 1, scale: 1, ease: "none",
              scrollTrigger: {
                trigger: element,
                start: "top 92%",
                end: "clamp(top 60%)",
                scrub: 0.8,
                invalidateOnRefresh: true,
              },
            });
          });
        });
        scheduleRefresh();
      }, root);
    }, root);

    function onAnchorClick(event) {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = event.target.closest?.("a[href]");
      if (!anchor || anchor.hasAttribute("download") || (anchor.target && anchor.target !== "_self")) return;
      const url = new URL(anchor.href, window.location.href);
      if (url.origin !== window.location.origin || url.pathname !== window.location.pathname || url.search !== window.location.search || !url.hash) return;
      let target;
      try { target = document.getElementById(decodeURIComponent(url.hash.slice(1))); } catch { return; }
      if (!target || !root.contains(target)) return;
      event.preventDefault();
      if (window.location.hash !== url.hash) window.history.pushState(null, "", url);
      pendingHash = url.hash;
      refreshLayout();
      scheduleRefresh();
    }

    function onHistoryNavigation() {
      pendingHash = window.location.hash;
      scheduleRefresh();
    }

    // Once the visitor takes over, late-loading assets must never pull them back.
    function releaseAnchor(event) {
      if (event.type === "keydown" && !["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Tab"].includes(event.key)) return;
      pendingHash = "";
    }

    root.addEventListener("click", onAnchorClick);
    root.addEventListener("load", scheduleRefresh, true);
    root.addEventListener("error", scheduleRefresh, true);
    window.addEventListener("hashchange", onHistoryNavigation);
    window.addEventListener("popstate", onHistoryNavigation);
    window.addEventListener("pageshow", onHistoryNavigation);
    const manualEvents = ["wheel", "touchstart", "pointerdown", "keydown"];
    manualEvents.forEach((name) => window.addEventListener(name, releaseAnchor, { passive: true }));
    const observer = new ResizeObserver(scheduleRefresh);
    observer.observe(root);
    if (nav) observer.observe(nav);
    document.fonts?.ready.then(scheduleRefresh);
    refreshLayout();
    scheduleRefresh();

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      cancelAnimationFrame(settlingFrame);
      observer.disconnect();
      root.removeEventListener("click", onAnchorClick);
      root.removeEventListener("load", scheduleRefresh, true);
      root.removeEventListener("error", scheduleRefresh, true);
      window.removeEventListener("hashchange", onHistoryNavigation);
      window.removeEventListener("popstate", onHistoryNavigation);
      window.removeEventListener("pageshow", onHistoryNavigation);
      manualEvents.forEach((name) => window.removeEventListener(name, releaseAnchor));
      media.revert();
      context.revert();
      if (previousOffset) root.style.setProperty("--site-nav-offset", previousOffset);
      else root.style.removeProperty("--site-nav-offset");
    };
  }, [containerRef, currentPath]);
}
