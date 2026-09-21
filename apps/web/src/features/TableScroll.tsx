import { useEffect, useRef, useState, type ReactNode } from "react";
/** Horizontal scroll container for tables. On narrow screens the right edge fades
 *  only while there is more to scroll, so a cut-off column reads as scrollable
 *  rather than broken; nothing is faded once the table fits or is at its end. */
export function TableScroll({ children }: { children: ReactNode }) {
  const box = useRef<HTMLDivElement>(null);
  const [more, setMore] = useState(false);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const update = () =>
      setMore(el.scrollWidth - el.clientWidth - el.scrollLeft > 1);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    el.addEventListener("scroll", update, { passive: true });
    return () => {
      observer.disconnect();
      el.removeEventListener("scroll", update);
    };
  }, [children]);
  return (
    <div ref={box} className={"table-scroll" + (more ? " has-more" : "")}>
      {children}
    </div>
  );
}
