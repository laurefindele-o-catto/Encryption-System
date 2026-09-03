import { useMemo } from "react";

export default function NoiseReveal({ active = false, width = 1100, height = 740 }) {
  const pattern = useMemo(() => {
    const shards = [];
    const random = (() => {
      let seed = 1337;
      return () => {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
      };
    })();

    for (let i = 0; i < 48; i += 1) {
      shards.push({
        x: Math.floor(random() * width),
        y: Math.floor(random() * height),
        size: 14 + Math.floor(random() * 32),
        rotation: Math.floor(random() * 360),
        opacity: 0.16 + random() * 0.24,
        narrow: 0.35 + random() * 0.4,
        bright: i % 7 === 0,
      });
    }

    return shards;
  }, [width, height]);

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        background: active ? "rgba(0, 0, 0, 0.72)" : "transparent",
        opacity: active ? 0.82 : 0,
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
          background: "transparent",
        }}
      >
        <defs>
          <linearGradient id="glassShardFill" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.52" />
            <stop offset="42%" stopColor="#dcecff" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#9bbde2" stopOpacity="0.06" />
          </linearGradient>
          <linearGradient id="brightGlassShardFill" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="42%" stopColor="#eaf4ff" stopOpacity="0.42" />
            <stop offset="100%" stopColor="#b9d7f4" stopOpacity="0.14" />
          </linearGradient>
        </defs>

        {pattern.map((shard, index) => {
          const points = `${shard.x},${shard.y - shard.size} ${shard.x + shard.size * shard.narrow},${shard.y - shard.size * 0.12} ${shard.x + shard.size * 0.2},${shard.y + shard.size} ${shard.x - shard.size * 0.58},${shard.y + shard.size * 0.28}`;
          return (
            <polygon
              key={`shard-${index}`}
              points={points}
              fill={`url(#${shard.bright ? "brightGlassShardFill" : "glassShardFill"})`}
              stroke={shard.bright ? "rgba(255, 255, 255, 0.88)" : "rgba(235, 246, 255, 0.55)"}
              strokeWidth={shard.bright ? "1.2" : "0.8"}
              strokeLinejoin="round"
              opacity={shard.bright ? Math.min(0.68, shard.opacity + 0.25) : shard.opacity}
              transform={`rotate(${shard.rotation} ${shard.x} ${shard.y})`}
            />
          );
        })}

      </svg>
    </div>
  );
}
