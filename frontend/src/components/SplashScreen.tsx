import { useState, useEffect, useRef } from 'react';

interface SplashScreenProps {
  /** Minimum time (ms) the splash is shown before starting the exit animation. */
  minDuration?: number;
  /** Called after the exit animation completes. */
  onFinished: () => void;
}

/**
 * Full-screen splash screen that shows the Marketidex logo with a cinematic
 * entrance animation, then gracefully exits to reveal the main app.
 */
export const SplashScreen: React.FC<SplashScreenProps> = ({
  minDuration = 2200,
  onFinished
}) => {
  const [phase, setPhase] = useState<'enter' | 'hold' | 'exit'>('enter');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Phase 1: enter → hold after a short delay so CSS transitions trigger
    const enterTimer = setTimeout(() => setPhase('hold'), 100);
    return () => clearTimeout(enterTimer);
  }, []);

  useEffect(() => {
    if (phase !== 'hold') return;
    // Phase 2: hold → exit after minDuration
    const holdTimer = setTimeout(() => setPhase('exit'), minDuration);
    return () => clearTimeout(holdTimer);
  }, [phase, minDuration]);

  useEffect(() => {
    if (phase !== 'exit') return;
    // Phase 3: exit animation then notify parent
    const exitTimer = setTimeout(onFinished, 800);
    return () => clearTimeout(exitTimer);
  }, [phase, onFinished]);

  const entered = phase === 'hold' || phase === 'exit';
  const exiting = phase === 'exit';

  return (
    <div
      ref={containerRef}
      className="splash-root"
      style={{
        opacity: exiting ? 0 : 1,
        transition: 'opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* Animated background grid */}
      <div className="splash-grid" />

      {/* Radial glow behind logo */}
      <div
        className="splash-glow"
        style={{
          transform: entered ? 'scale(1)' : 'scale(0)',
          opacity: entered ? 1 : 0,
          transition: 'transform 1.2s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.8s ease',
        }}
      />

      {/* Logo container */}
      <div
        className="splash-logo-group"
        style={{
          transform: entered
            ? exiting
              ? 'scale(0.92) translateY(-8px)'
              : 'scale(1) translateY(0)'
            : 'scale(0.6) translateY(20px)',
          opacity: entered ? (exiting ? 0 : 1) : 0,
          transition: exiting
            ? 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s ease'
            : 'transform 0.9s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.7s ease',
        }}
      >
        {/* SVG logo icon — ascending bars with AI spark */}
        <div className="splash-icon-wrap">
          <svg
            viewBox="0 0 64 64"
            width="80"
            height="80"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="splash-grad" x1="0" y1="64" x2="64" y2="0">
                <stop offset="0%" stopColor="#5b9cec" />
                <stop offset="100%" stopColor="#863bff" />
              </linearGradient>
              <filter id="splash-glow-filter">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Bar 1 — short */}
            <rect
              x="6" y="42" width="10" height="16" rx="2"
              fill="url(#splash-grad)"
              className="splash-bar splash-bar-1"
            />
            {/* Bar 2 — medium */}
            <rect
              x="20" y="30" width="10" height="28" rx="2"
              fill="url(#splash-grad)"
              className="splash-bar splash-bar-2"
            />
            {/* Bar 3 — tall */}
            <rect
              x="34" y="18" width="10" height="40" rx="2"
              fill="url(#splash-grad)"
              className="splash-bar splash-bar-3"
            />
            {/* Bar 4 — tallest */}
            <rect
              x="48" y="8" width="10" height="50" rx="2"
              fill="url(#splash-grad)"
              className="splash-bar splash-bar-4"
            />

            {/* AI spark / neural node */}
            <g filter="url(#splash-glow-filter)">
              <circle cx="53" cy="8" r="3" fill="#c084fc" className="splash-spark" />
              <line x1="53" y1="4" x2="53" y2="1" stroke="#c084fc" strokeWidth="1.5" strokeLinecap="round" className="splash-spark" />
              <line x1="56.5" y1="5.5" x2="58.5" y2="3.5" stroke="#c084fc" strokeWidth="1.5" strokeLinecap="round" className="splash-spark" />
              <line x1="57" y1="8" x2="60" y2="8" stroke="#c084fc" strokeWidth="1.5" strokeLinecap="round" className="splash-spark" />
            </g>

            {/* Ascending trend line */}
            <path
              d="M8 52 L23 38 L37 28 L52 14"
              stroke="url(#splash-grad)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeDasharray="60"
              className="splash-trend-line"
              fill="none"
              opacity="0.5"
            />
          </svg>
        </div>

        {/* Wordmark */}
        <div className="splash-wordmark">
          <span className="splash-title">Marketidex</span>
          <span className="splash-subtitle">Intelijen Pasar IDX</span>
        </div>
      </div>

      {/* Particle ring effect */}
      <div className="splash-particles" aria-hidden="true">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="splash-particle"
            style={{
              '--i': i,
              '--total': 12,
            } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  );
};
