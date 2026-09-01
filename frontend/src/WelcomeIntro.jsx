import { useEffect, useState } from 'react';
import './App.css';

export default function WelcomeIntro({ onDone }) {
  const [exit, setExit] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setExit(true);
      setTimeout(onDone, 500); // Wait for exit animation
    }, 3000); // 3 seconds intro
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div className={`intro-screen ${exit ? 'exit' : ''}`}>
      <div className="intro-eyebrow">OMNIONCO AI</div>
      <div className="intro-title">OmniOnco <em>AI</em></div>
      <div className="intro-wave show">
        <span className="intro-spark"></span>
      </div>
      <div className="intro-mark">v1.0</div>
    </div>
  );
}
