"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type UseScrollSpyOptions = {
  /** Distance from viewport top where the active step switches (px). */
  offsetTop?: number;
  enabled?: boolean;
};

export function useScrollSpy(itemCount: number, options: UseScrollSpyOptions = {}) {
  const { offsetTop = 116, enabled = true } = options;
  const [activeIndex, setActiveIndex] = useState(0);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);
  const containerRef = useRef<HTMLElement | null>(null);

  const setItemRef = useCallback(
    (index: number) => (node: HTMLElement | null) => {
      itemRefs.current[index] = node;
      if (index === 0 && node?.parentElement) {
        containerRef.current = node.parentElement;
      }
    },
    []
  );

  useEffect(() => {
    if (!enabled || itemCount === 0) return;

    const update = () => {
      const elements = itemRefs.current.filter((node): node is HTMLElement => node !== null);
      if (elements.length === 0) return;

      const anchor = offsetTop;
      const last = elements[elements.length - 1];
      const lastRect = last.getBoundingClientRect();
      const container = containerRef.current;
      const containerRect = container?.getBoundingClientRect();

      // Keep the last step active while there is still walkthrough scroll room below it.
      if (containerRect && containerRect.bottom > window.innerHeight * 0.45) {
        if (lastRect.top <= anchor) {
          setActiveIndex(elements.length - 1);
          return;
        }
      } else if (containerRect && containerRect.bottom <= window.innerHeight * 0.45) {
        setActiveIndex(elements.length - 1);
        return;
      }

      let next = 0;
      for (let i = 0; i < elements.length; i++) {
        const top = elements[i].getBoundingClientRect().top;
        if (top <= anchor + 8) {
          next = i;
        }
      }
      setActiveIndex(next);
    };

    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [enabled, itemCount, offsetTop]);

  return { activeIndex, setItemRef };
}
