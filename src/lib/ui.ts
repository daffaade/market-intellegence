import type { Direction } from './format';

export type Tone = 'neutral' | 'up' | 'down' | 'warn' | 'accent';

export const cx = (...classes: Array<string | false | null | undefined>) =>
  classes.filter(Boolean).join(' ');

export const directionTone = (d: Direction): Tone => (d === 'BULLISH' ? 'up' : d === 'BEARISH' ? 'down' : 'neutral');
