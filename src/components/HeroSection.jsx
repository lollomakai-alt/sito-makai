import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";

// Similar-sized, full-proportion prints on a 1400 × 480 canvas.
const wallPhotos = [
  { src: "eventi.webp", x: 10, y: 10, w: 174.217, h: 228.743, rotate: -1.0, layer: 1 },
  { src: "SALA.webp", x: 10, y: 234.569, w: 192.702, h: 231.431, rotate: 1.3, layer: 2 },
  { src: "drink2.webp", x: 180.217, y: 16, w: 178.235, h: 234.905, rotate: -1.5, layer: 3 },
  { src: "statua.webp", x: 198.702, y: 220.019, w: 187.433, h: 249.981, rotate: -0.6, layer: 1 },
  { src: "sala12.webp", x: 354.452, y: 12, w: 170.02, h: 225.107, rotate: 1.1, layer: 2 },
  { src: "SALA7.webp", x: 382.135, y: 237.198, w: 188.847, h: 226.802, rotate: -1.0, layer: 1 },
  { src: "IMG_4642.webp", x: 520.472, y: 19, w: 184.083, h: 223.026, rotate: 1.4, layer: 2 },
  { src: "sala5-converted.webp", x: 566.982, y: 282.369, w: 247.508, h: 185.631, rotate: -0.8, layer: 3 },
  { src: "statua2.webp", x: 700.555, y: 13, w: 171.129, h: 228.236, rotate: -1.3, layer: 1 },
  { src: "drink.webp", x: 810.49, y: 259.23, w: 214.505, h: 203.77, rotate: 1.2, layer: 2 },
  { src: "chi-siamo.webp", x: 867.684, y: 17, w: 177.529, h: 233.543, rotate: 0.6, layer: 2 },
  { src: "Tiki mug .webp", x: 1020.995, y: 226.522, w: 191.353, h: 242.478, rotate: -1.2, layer: 3 },
  { src: "Drink10.webp", x: 1041.213, y: 11, w: 174.853, h: 221.124, rotate: 1.6, layer: 1 },
  { src: "Chi siamo 2 .webp", x: 1208.347, y: 226.802, w: 181.653, h: 238.198, rotate: -0.9, layer: 2 },
  { src: "Drink 11.webp", x: 1212.066, y: 15, w: 177.934, h: 223.964, rotate: 1.0, layer: 1 },
];

function PhotoWall() {
  const trackRef = useRef(null);
  const animationRef = useRef(null);

  useLayoutEffect(() => {
    const track = trackRef.current;
    const composition = track.firstElementChild;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    // Keep a steady, visible drift of 22px/s across desktop and mobile widths.
    const getDuration = () => Math.max(composition.getBoundingClientRect().width, 1) / 22;
    const context = gsap.context(() => {
      animationRef.current = gsap.fromTo(
        track,
        { xPercent: -50 },
        {
          xPercent: 0,
          duration: getDuration(),
          ease: "none",
          repeat: -1,
          paused: reducedMotion.matches,
        }
      );
    }, track);
    const resizeObserver = new ResizeObserver(() => {
      animationRef.current?.duration(getDuration());
    });
    resizeObserver.observe(composition);
    const onMotionChange = () => animationRef.current?.paused(reducedMotion.matches);
    reducedMotion.addEventListener("change", onMotionChange);

    return () => {
      resizeObserver.disconnect();
      reducedMotion.removeEventListener("change", onMotionChange);
      context.revert();
      animationRef.current = null;
    };
  }, []);

  return (
    <div className="hero-wall">
      <div ref={trackRef} className="hero-wall-track">
        {[0, 1].map((copy) => (
          <div
            key={copy}
            className="hero-wall-composition"
            role={copy === 0 ? "img" : undefined}
            aria-label={copy === 0 ? "Parete fotografica del Makai: sala, cocktail, dettagli Tiki e serate nel locale" : undefined}
            aria-hidden={copy === 1 ? true : undefined}
          >
            {wallPhotos.map((photo) => (
              <figure
                key={photo.src}
                className="hero-wall-item"
                style={{
                  "--x": `${(photo.x / 1400) * 100}%`,
                  "--y": `${(photo.y / 480) * 100}%`,
                  "--w": `${(photo.w / 1400) * 100}%`,
                  "--h": `${(photo.h / 480) * 100}%`,
                  "--mobile-x": `${((photo.x - photo.w * 0.125) / 1400) * 100}%`,
                  "--mobile-y": `${((photo.y - photo.h * 0.125) / 480) * 100}%`,
                  "--mobile-w": `${((photo.w * 1.25) / 1400) * 100}%`,
                  "--mobile-h": `${((photo.h * 1.25) / 480) * 100}%`,
                  "--r": `${photo.rotate || 0}deg`,
                  "--z": photo.layer,
                }}
              >
                <picture>
                  <source
                    media="(max-width: 600px)"
                    srcSet={`${import.meta.env.BASE_URL}images/hero/${photo.src} 1x, ${import.meta.env.BASE_URL}images/hero/mobile/${photo.src} 2x, ${import.meta.env.BASE_URL}images/${photo.src} 3x`}
                  />
                  <img
                    src={`${import.meta.env.BASE_URL}images/hero/${photo.src}`}
                    alt=""
                    decoding="async"
                    draggable={false}
                  />
                </picture>
              </figure>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function HeroSection() {
  const sectionRef = useRef(null);

  useLayoutEffect(() => {
    const section = sectionRef.current;
    const nav = document.querySelector(".top-nav");
    if (!nav) return undefined;

    const reserveNavSpace = () => {
      section.style.setProperty("--hero-nav-height", `${nav.getBoundingClientRect().height}px`);
    };
    reserveNavSpace();
    const observer = new ResizeObserver(reserveNavSpace);
    observer.observe(nav);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} id="hero" className="hero-section" aria-labelledby="hero-title">
      <PhotoWall />
      <div className="hero-content">
        <h1 id="hero-title" className="gold-text">Benvenuti a bordo del Makai</h1>
        <p className="hero-description">
          Anima Tiki, spirito d'avventura e sapori esotici in un viaggio fuori dall'ordinario.
        </p>
      </div>
    </section>
  );
}
