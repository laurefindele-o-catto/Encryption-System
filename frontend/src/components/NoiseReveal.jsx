import { useMemo } from "react";

export default function NoiseReveal({ active = false, width = 1100, height = 740 }) {
  const pattern = useMemo(() => {
    const dots = [];
    const random = (() => {
      let seed = 1337;
      return () => {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
      };
    })();

    for (let i = 0; i < 2400; i += 1) {
      const x = Math.floor(random() * width);
      const y = Math.floor(random() * height);
      const brightness = 200 + Math.floor(random() * 55);
      const blue = Math.random() < 0.08;
      dots.push({ x, y, brightness, blue, size: Math.random() < 0.2 ? 2 : 1.5 });
    }

    return dots;
  }, [width, height]);

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        background: active ? "#000000" : "transparent",
        opacity: active ? 1 : 0,
        transition: "opacity 0.35s ease",
        zIndex: 0,
      }}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid slice"
        style={{
          width: "100vw",
          height: "100vh",
          display: "block",
          background: "#000",
        }}
      >
        {pattern.map((dot, index) => (
          <circle
            key={`${dot.x}-${dot.y}-${index}`}
            cx={dot.x}
            cy={dot.y}
            r={dot.size}
            fill={dot.blue ? `rgba(50, 130, 255, ${0.8 + (dot.x + dot.y) % 3 * 0.05})` : `rgba(${dot.brightness}, ${dot.brightness}, ${dot.brightness}, 0.95)`}
            opacity={dot.blue ? 0.9 : 1}
          />
        ))}

        <g opacity={active ? 1 : 0}>
          {Array.from({ length: 140 }).map((_, i) => {
            const x = 18 + ((i * 13) % 180);
            const y = 18 + ((i * 17) % 180);
            const hasBlue = i % 5 === 0;
            return (
              <circle
                key={`reveal-${i}`}
                cx={x}
                cy={y}
                r={hasBlue ? 2.1 : 1.6}
                fill={hasBlue ? "rgba(55, 130, 255, 0.95)" : "rgba(255,255,255,0.96)"}
              />
            );
          })}
        </g>
      </svg>
    </div>
  );
}
