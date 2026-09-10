import {compileDiagramSpec} from "./diagram-compiler.mjs";

const esc=(value)=>String(value??"").replace(/[&<>"']/gu,(c)=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&apos;"}[c]));
const num=(value,fallback=0)=>Number.isFinite(Number(value))?Number(value):fallback;

export function buildDiagramPreviewSvg(spec,durationSeconds,options={}){
  const graphic=compileDiagramSpec(spec,durationSeconds,options);
  const parts=[`<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 720 1280" preserveAspectRatio="xMidYMid meet">`,`<rect width="720" height="1280" fill="${esc(graphic.background||'#08111F')}"/>`,`<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#FFB454"/></marker></defs>`];
  if(graphic.title)parts.push(`<text x="360" y="90" fill="#F7FAFC" font-size="34" font-weight="700" font-family="DejaVu Sans,Arial,sans-serif" text-anchor="middle">${esc(graphic.title)}</text>`);
  for(const e of graphic.elements){
    if(e.type==='rect')parts.push(`<rect x="${num(e.x)}" y="${num(e.y)}" width="${num(e.width)}" height="${num(e.height)}" rx="${num(e.rx)}" fill="${esc(e.fill||'none')}" stroke="${esc(e.stroke||'none')}" stroke-width="${num(e.strokeWidth)}"/>`);
    else if(e.type==='circle')parts.push(`<circle cx="${num(e.cx)}" cy="${num(e.cy)}" r="${num(e.r)}" fill="${esc(e.fill||'none')}" stroke="${esc(e.stroke||'none')}" stroke-width="${num(e.strokeWidth)}"/>`);
    else if(e.type==='line')parts.push(`<line x1="${num(e.x1)}" y1="${num(e.y1)}" x2="${num(e.x2)}" y2="${num(e.y2)}" stroke="${esc(e.stroke||'#fff')}" stroke-width="${num(e.strokeWidth,5)}" stroke-linecap="round"${e.arrow?' marker-end="url(#arrow)"':''}/>`);
    else if(e.type==='polygon'){const points=(Array.isArray(e.points)?e.points:[]).map(([x,y])=>`${num(x)},${num(y)}`).join(' ');parts.push(`<polygon points="${points}" fill="${esc(e.fill||'none')}" stroke="${esc(e.stroke||'none')}" stroke-width="${num(e.strokeWidth)}"/>`);}
    else if(e.type==='text')parts.push(`<text x="${num(e.x)}" y="${num(e.y)}" fill="${esc(e.fill||'#fff')}" font-size="${num(e.fontSize,28)}" font-weight="${num(e.fontWeight,600)}" font-family="DejaVu Sans,Arial,sans-serif" text-anchor="middle">${esc(e.text)}</text>`);
  }
  parts.push('</svg>');
  return {svg:parts.join(''),graphic};
}
