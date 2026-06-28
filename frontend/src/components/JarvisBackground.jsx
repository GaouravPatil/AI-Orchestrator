import { useEffect, useRef } from 'react';

/* ─── Jarvis Animated Background Canvas ─────────────────────────────
   Three layered effects:
   1. Particle network — floating nodes connected by lines
   2. Radar sweep — rotating cyan arc
   3. Hex grid — subtle tiled hexagons
────────────────────────────────────────────────────────────────────── */
export default function JarvisBackground({ intensity = 1 }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // -- Resize --
    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // -- Particles --
    const PARTICLE_COUNT = Math.floor(60 * intensity);
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:    Math.random() * canvas.width,
      y:    Math.random() * canvas.height,
      vx:   (Math.random() - 0.5) * 0.35,
      vy:   (Math.random() - 0.5) * 0.35,
      r:    Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.5 + 0.15,
    }));

    // -- Radar --
    let radarAngle = 0;

    // -- Draw hex grid (pre-rendered into offscreen canvas) --
    const hexCanvas = document.createElement('canvas');
    hexCanvas.width  = canvas.width  || window.innerWidth;
    hexCanvas.height = canvas.height || window.innerHeight;
    const hx = hexCanvas.getContext('2d');
    const S = 38; // hex size
    const drawHex = (cx, cy) => {
      hx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i - Math.PI / 6;
        const px = cx + S * Math.cos(angle);
        const py = cy + S * Math.sin(angle);
        i === 0 ? hx.moveTo(px, py) : hx.lineTo(px, py);
      }
      hx.closePath();
    };
    const cols = Math.ceil(hexCanvas.width  / (S * 1.73)) + 2;
    const rows = Math.ceil(hexCanvas.height / (S * 1.5))  + 2;
    hx.strokeStyle = 'rgba(0,212,255,0.04)';
    hx.lineWidth   = 0.6;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cx = c * S * 1.73 + (r % 2 ? S * 0.865 : 0);
        const cy = r * S * 1.5;
        drawHex(cx, cy);
        hx.stroke();
      }
    }

    // -- Animation loop --
    const MAX_DIST = 140;

    const tick = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Hex grid
      ctx.drawImage(hexCanvas, 0, 0);

      // Move + wrap particles
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width)  p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
      });

      // Connection lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d  = Math.sqrt(dx * dx + dy * dy);
          if (d < MAX_DIST) {
            const alpha = (1 - d / MAX_DIST) * 0.18 * intensity;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(0,212,255,${alpha})`;
            ctx.lineWidth   = 0.6;
            ctx.stroke();
          }
        }
      }

      // Particles
      particles.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,212,255,${p.alpha})`;
        ctx.fill();
        // glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,136,255,${p.alpha * 0.25})`;
        ctx.fill();
      });

      // Radar sweep
      const cx = canvas.width  * 0.82;
      const cy = canvas.height * 0.18;
      const R  = Math.min(canvas.width, canvas.height) * 0.14;

      // Radar rings
      [1, 0.66, 0.33].forEach((f, i) => {
        ctx.beginPath();
        ctx.arc(cx, cy, R * f, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0,212,255,${0.06 - i * 0.01})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      });

      // Sweep gradient
      radarAngle += 0.012;
      const sweep = ctx.createConicalGradient
        ? null // not standard – use workaround
        : null;
      // Workaround: fill a sector
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(radarAngle);
      const grad = ctx.createLinearGradient(0, 0, R, 0);
      grad.addColorStop(0,   'rgba(0,212,255,0.18)');
      grad.addColorStop(0.7, 'rgba(0,212,255,0.06)');
      grad.addColorStop(1,   'rgba(0,212,255,0)');
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, R, -0.5, 0.5);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Sweep tip line
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(R, 0);
      ctx.strokeStyle = 'rgba(0,212,255,0.5)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();

      // Centre dot
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,212,255,0.8)';
      ctx.fill();

      // Bottom-left corner decoration
      const bx = 0, by = canvas.height;
      ctx.save();
      ctx.strokeStyle = 'rgba(0,212,255,0.07)';
      ctx.lineWidth = 1;
      [60, 120, 180].forEach(rad => {
        ctx.beginPath();
        ctx.arc(bx, by, rad, -Math.PI / 2, 0);
        ctx.stroke();
      });
      ctx.restore();

      animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [intensity]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
}
