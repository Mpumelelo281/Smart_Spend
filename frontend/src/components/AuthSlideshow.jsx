import { useEffect, useState } from "react";

// Compressed from the original 11-22MB source photos down to ~60-190KB
// each (WebP with JPEG fallback) — see the resize step in the repo
// history. Mobile data is expensive for this user base; a login-page
// background is not worth megabytes of it.
const SLIDES = ["slide-1", "slide-2", "slide-3"];
const INTERVAL_MS = 6000;

function prefersReducedMotion() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

export default function AuthSlideshow({ className = "" }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion()) return; // static first image, no auto-advance
    const id = setInterval(() => setIndex((i) => (i + 1) % SLIDES.length), INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={`absolute inset-0 ${className}`} aria-hidden="true">
      {SLIDES.map((name, i) => (
        <picture key={name}>
          <source srcSet={`/images/${name}.webp`} type="image/webp" />
          <img
            src={`/images/${name}.jpg`}
            alt=""
            className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-[1500ms] ease-in-out ${
              i === index ? "opacity-100" : "opacity-0"
            }`}
            loading={i === 0 ? "eager" : "lazy"}
          />
        </picture>
      ))}
    </div>
  );
}
