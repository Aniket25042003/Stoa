"use client";

import { useEffect, useState } from "react";

export function useMarketingWebGL() {
  const [shouldRenderWebGL, setShouldRenderWebGL] = useState(false);
  const [dpr, setDpr] = useState(1);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) {
      setShouldRenderWebGL(false);
      return;
    }

    // Skip WebGL on small phones — video + posters are enough
    if (window.innerWidth < 480) {
      setShouldRenderWebGL(false);
      return;
    }

    try {
      const canvas = document.createElement("canvas");
      const support = !!(
        window.WebGLRenderingContext &&
        (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
      );
      if (!support) {
        setShouldRenderWebGL(false);
        return;
      }
    } catch {
      setShouldRenderWebGL(false);
      return;
    }

    setShouldRenderWebGL(true);

    const checkDpr = () => {
      const w = window.innerWidth;
      if (w < 768) setDpr(1);
      else if (w < 1200) setDpr(1.15);
      else setDpr(1.25);
    };

    checkDpr();
    window.addEventListener("resize", checkDpr, { passive: true });
    return () => window.removeEventListener("resize", checkDpr);
  }, []);

  return { shouldRenderWebGL, dpr };
}
