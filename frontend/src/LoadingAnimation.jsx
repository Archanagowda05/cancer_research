import { useEffect, useRef } from 'react';

export default function LoadingAnimation() {
  const markRef = useRef(null);
  const waveRef = useRef(null);
  const eyebrowRef = useRef(null);
  const titleRef = useRef(null);
  const pathRef = useRef(null);
  const n0Ref = useRef(null);
  const n1Ref = useRef(null);
  const n2Ref = useRef(null);
  const n3Ref = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const mark = markRef.current;
    const wave = waveRef.current;
    const eyebrow = eyebrowRef.current;
    const title = titleRef.current;
    const path = pathRef.current;
    const nodes = [n0Ref.current, n1Ref.current, n2Ref.current, n3Ref.current];

    if (!mark || !wave || !path) return;

    // Reset animations
    cancelAnimationFrame(rafRef.current);
    [mark, eyebrow, title].forEach(el => { 
      if(el) {
        el.style.animation = 'none'; 
        void el.offsetWidth; 
      }
    });
    if(wave) wave.style.opacity = '0';
    
    // Trigger animations
    if(mark) mark.style.animation = 'ointroSlide .7s cubic-bezier(.2,.7,.3,1) both';
    
    setTimeout(() => { 
      if(wave) {
        wave.style.transition = 'opacity .5s ease'; 
        wave.style.opacity = '1'; 
      }
    }, 300);
    
    if(eyebrow) eyebrow.style.animation = 'ointroFade .6s ease .3s both';
    if(title) title.style.animation = 'ointroRise .7s cubic-bezier(.2,.7,.3,1) .55s both';
    
    const len = path.getTotalLength();
    const start = performance.now();
    const dur = 2600;
    
    function tick(ts) {
      const t = (ts - start) % dur;
      nodes.forEach((el, i) => {
        if (!el) return;
        const off = ((t / dur) + (i / nodes.length)) % 1;
        const pt = path.getPointAtLength(off * len);
        el.setAttribute('cx', pt.x);
        el.setAttribute('cy', pt.y);
      });
      rafRef.current = requestAnimationFrame(tick);
    }
    
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100%' }}>
      <style>{`
        @keyframes ointroSlide { from { opacity: 0; transform: translateX(-16px) } to { opacity: 1; transform: translateX(0) } }
        @keyframes ointroFade { from { opacity: 0 } to { opacity: 1 } }
        @keyframes ointroRise { from { opacity: 0; transform: translateY(14px) scale(.97) } to { opacity: 1; transform: translateY(0) scale(1) } }
        @keyframes ospark { 0%, 100% { opacity: 0; transform: scale(.5) } 50% { opacity: 1; transform: scale(1) } }
        .ospark { position: absolute; width: 3px; height: 3px; border-radius: 50%; background: #B4791E; }
      `}</style>
      <div style={{
        position: 'relative', width: '100%', maxWidth: '520px', height: '320px', 
        background: '#0A0F0E', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', 
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', 
        gap: '14px', overflow: 'hidden'
      }}>
        <span className="ospark" style={{ top: '40px', left: '60px', animation: 'ospark 2.4s ease-in-out infinite .2s' }}></span>
        <span className="ospark" style={{ top: '70px', right: '70px', animation: 'ospark 2.4s ease-in-out infinite .9s' }}></span>
        <span className="ospark" style={{ bottom: '60px', left: '90px', animation: 'ospark 2.4s ease-in-out infinite 1.4s' }}></span>

        <div ref={markRef} style={{
          fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '.16em', 
          border: '1px solid #00b4d8', padding: '4px 10px', borderRadius: '2px', color: '#00b4d8'
        }}>OMN</div>

        <svg ref={waveRef} width="280" height="30" viewBox="0 0 280 30" style={{ opacity: 0 }}>
          <path ref={pathRef} d="M0,15 C46,2 93,28 140,15 C186,2 233,28 280,15" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5"></path>
          <circle ref={n0Ref} r="4" fill="#38a169"></circle>
          <circle ref={n1Ref} r="4" fill="#00b4d8"></circle>
          <circle ref={n2Ref} r="4" fill="#ed8936"></circle>
          <circle ref={n3Ref} r="4" fill="#9f7aea"></circle>
        </svg>

        <div ref={eyebrowRef} style={{
          fontFamily: 'var(--font-mono)', fontSize: '11px', letterSpacing: '.18em', color: '#92A6A2', opacity: 0
        }}>INITIALIZING OMNIONCO PIPELINE</div>
        
        <div ref={titleRef} style={{
          fontFamily: 'Inter, sans-serif', fontSize: '38px', fontWeight: 500, color: '#ffffff', opacity: 0
        }}>OmniOnco <em style={{ fontStyle: 'italic', color: '#00b4d8' }}>AI</em></div>
      </div>
    </div>
  );
}
