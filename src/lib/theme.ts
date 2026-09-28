import { createContext, useContext } from 'react';

export type Theme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'marketidex_theme';

export const readInitialTheme = (): Theme => {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // storage unavailable — fall through to OS preference
  }
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
};

export const applyTheme = (theme: Theme): void => {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // ignore
  }
};

/**
 * Recharts writes colors as SVG attributes, so charts get concrete hex values
 * per theme instead of CSS variables. Keep in sync with index.css.
 */
export const CHART_COLORS: Record<Theme, {
  grid: string;
  axis: string;
  ink: string;
  muted: string;
  context: string;
  surface: string;
  series1: string;
  series2: string;
  up: string;
  down: string;
  warn: string;
}> = {
  light: {
    grid: '#e9e7e1',
    axis: '#86847d',
    ink: '#161615',
    muted: '#4f4e4a',
    context: '#cfccc4',
    surface: '#fcfcfb',
    series1: '#2a78d6',
    series2: '#eb6834',
    up: '#16875a',
    down: '#cf3a3a',
    warn: '#a86b00'
  },
  dark: {
    grid: '#242422',
    axis: '#7c7b74',
    ink: '#ecebe6',
    muted: '#b1b0a8',
    context: '#3a3a36',
    surface: '#171716',
    series1: '#3987e5',
    series2: '#d95926',
    up: '#3fb68b',
    down: '#e66767',
    warn: '#e0a43a'
  }
};

export const ThemeContext = createContext<Theme>('dark');

export const useChartColors = () => CHART_COLORS[useContext(ThemeContext)];
