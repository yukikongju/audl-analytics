/* theme.js — single source for the palette used by JS-drawn charts.
   Mirrors the CSS custom properties in css/base.css so canvas/SVG
   code (which can't read CSS vars cheaply) shares the same colors. */

export const P = {
  bg:     '#0A0E14',
  panel:  '#121821',
  panel2: '#1A222D',
  line:   '#25303C',
  text:   '#E7EDF3',
  dim:    '#8592A0',
  orange: '#FF6A2B',
  lime:   '#C6FF3D',
  blue:   '#3FA7FF',
  red:    '#FF4D6A',
  purple: '#B98CFF',
  teal:   '#2DD4BF',
  home:   '#4A7FB5',
  away:   '#E8A838',
  team:   '#D4622B',
};
