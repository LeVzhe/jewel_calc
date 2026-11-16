import { useEffect, useState, type TransitionEvent } from "react";
import type { JewelryPhoto } from "../types";

const INTERVAL_MS = 6000;

type Direction = 1 | -1;
type Phase = "idle" | "ready" | "move";

type Props = {
  photos: JewelryPhoto[];
  playing: boolean;
  onOpen: () => void;
};

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function PhotoCarousel({ photos, playing, onOpen }: Props) {
  const [index, setIndex] = useState(0);
  const [incoming, setIncoming] = useState<number | null>(null);
  const [direction, setDirection] = useState<Direction>(1);
  const [phase, setPhase] = useState<Phase>("idle");
  const count = photos.length;
  const safe = count === 0 ? 0 : Math.min(index, count - 1);
  const current = photos[safe];
  const nextPhoto = incoming === null ? null : photos[incoming];

  useEffect(() => {
    if (playing || phase !== "idle" || index === 0) return;
    setIndex(0);
  }, [playing, phase, index]);

  useEffect(() => {
    if (phase !== "ready") return;
    let second = 0;
    const first = window.requestAnimationFrame(() => {
      second = window.requestAnimationFrame(() => setPhase("move"));
    });
    return () => {
      window.cancelAnimationFrame(first);
      window.cancelAnimationFrame(second);
    };
  }, [phase]);

  function begin(target: number, dir: Direction) {
    if (count < 2 || phase !== "idle" || target === safe) return;
    const next = (target + count) % count;
    if (reducedMotion()) {
      setIndex(next);
      return;
    }
    setDirection(dir);
    setIncoming(next);
    setPhase("ready");
  }

  useEffect(() => {
    if (!playing || count < 2 || phase !== "idle") return;
    const timer = window.setInterval(() => {
      if (document.hidden) return;
      const next = (index + 1) % count;
      if (reducedMotion()) {
        setIndex(next);
        return;
      }
      setDirection(1);
      setIncoming(next);
      setPhase("ready");
    }, INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [playing, count, phase, index]);

  function finish(event: TransitionEvent<HTMLSpanElement>) {
    if (event.target !== event.currentTarget || event.propertyName !== "transform") return;
    if (phase !== "move" || incoming === null) return;
    setIndex(incoming);
    setIncoming(null);
    setPhase("idle");
  }

  if (!current) return <span className="card-fallback" />;

  const sliding = nextPhoto !== null && phase !== "idle";
  const slides = !sliding || !nextPhoto ? [current] : direction === 1 ? [current, nextPhoto] : [nextPhoto, current];
  const shift = !sliding ? 0 : direction === 1 ? (phase === "move" ? -100 : 0) : phase === "move" ? 0 : -100;
  const marked = incoming ?? safe;

  return (
    <div className="carousel">
      <button type="button" className="carousel-frame" onClick={onOpen}>
        <span
          className={phase === "move" ? "carousel-track is-move" : "carousel-track"}
          style={{ transform: `translateX(${shift}%)` }}
          onTransitionEnd={finish}
        >
          {slides.map((photo, position) => (
            <img key={`${photo.id}-${position}`} src={photo.image_preview} alt="" />
          ))}
        </span>
      </button>
      {count > 1 ? (
        <>
          <button
            type="button"
            className="carousel-nav prev"
            aria-label="Предыдущее фото"
            onClick={() => begin(safe - 1, -1)}
          >
            ‹
          </button>
          <button
            type="button"
            className="carousel-nav next"
            aria-label="Следующее фото"
            onClick={() => begin(safe + 1, 1)}
          >
            ›
          </button>
          <div className="carousel-dots">
            {photos.map((photo, dot) => (
              <button
                key={photo.id}
                type="button"
                aria-label={`Фото ${dot + 1}`}
                aria-current={dot === marked ? "true" : undefined}
                onClick={() => begin(dot, dot > safe ? 1 : -1)}
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
