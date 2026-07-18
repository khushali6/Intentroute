import React from 'react';
import './index.css';

const Ticker = ({ items, speed = '30s' }) => {
  return (
    <div style={{
      width: '100%',
      maxWidth: '500px',
      height: '36px',
      overflow: 'hidden',
      position: 'relative',
      maskImage: 'linear-gradient(90deg, transparent 0%, black 12%, black 88%, transparent 100%)',
      WebkitMaskImage: 'linear-gradient(90deg, transparent 0%, black 12%, black 88%, transparent 100%)',
    }}>
      <div style={{
        display: 'flex',
        width: 'max-content',
        animation: `marquee-left ${speed} linear infinite`,
      }}>
        {/* Repeat 4x for seamless loop */}
        {[...Array(4)].map((_, i) => (
          <div key={i} style={{ display: 'flex', gap: '12px', paddingRight: '12px' }}>
            {items.map((item, j) => (
              <div key={j} style={{
                fontSize: '13px',
                fontWeight: 500,
                color: 'var(--muted)',
                padding: '6px 14px',
                borderRadius: '99px',
                backgroundColor: 'rgb(251, 251, 251)',
                whiteSpace: 'nowrap'
              }}>
                {item}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

const CurvedLines = ({ side }) => {
  const isLeft = side === 'left';
  return (
    <div style={{
      position: 'absolute',
      [isLeft ? 'left' : 'right']: 0,
      top: '50%',
      transform: 'translateY(-50%)',
      height: '80%',
      width: '30%',
      pointerEvents: 'none',
      overflow: 'hidden'
    }}>
      {[...Array(20)].map((_, i) => (
        <div key={i} style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          [isLeft ? 'left' : 'right']: `${i * 10}px`,
          width: `${60 + (i * 10)}px`,
          border: '2.5px solid #FCFAF8',
          borderLeft: isLeft ? 'none' : '2.5px solid #FCFAF8',
          borderRight: !isLeft ? 'none' : '2.5px solid #FCFAF8',
          borderTopRightRadius: isLeft ? '80%' : 0,
          borderBottomRightRadius: isLeft ? '80%' : 0,
          borderTopLeftRadius: !isLeft ? '80%' : 0,
          borderBottomLeftRadius: !isLeft ? '80%' : 0,
          animation: 'line-pulse 5s ease-in-out infinite',
          animationDelay: `${i * 0.25}s`,
          opacity: 0
        }} />
      ))}
    </div>
  );
};

export const Hero = () => {
  return (
    <section style={{
      minHeight: '850px',
      padding: '160px 36px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background Image */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'url(https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260626_041422_4a459e05-abce-4150-9fb7-4ededc423cd1.png&w=1280&q=85)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        zIndex: -2
      }} />

      {/* Decorative Lines */}
      <CurvedLines side="left" />
      <CurvedLines side="right" />

      {/* Progressive blur mask at bottom */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: '178px',
        background: 'linear-gradient(to bottom, transparent, rgba(255,255,255,0.4) 40%, white)',
        zIndex: -1
      }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <Ticker items={["LLM Intent Parsing", "USDA Nutrition API", "TheMealDB Catalog", "LangGraph State", "MCP Tooling"]} />

        <h1 style={{
          maxWidth: '650px',
          fontSize: '82px',
          lineHeight: 1.03,
          letterSpacing: '-0.07em',
          fontWeight: 600,
          marginTop: '32px',
          marginBottom: '24px'
        }}>
          Fuzzy intent to <span className="serif italic" style={{ letterSpacing: '-0.08em' }}>structured</span> orders.
        </h1>

        <p style={{
          maxWidth: '476px',
          fontSize: '17px',
          lineHeight: 1.45,
          fontWeight: 400,
          color: 'var(--muted)',
          marginBottom: '40px'
        }}>
          Skip the endless browsing. State what you need, and the IntentRoute agent will perfectly map your nutritional constraints.
        </p>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <button className="primary-button" onClick={() => window.scrollTo({top: 850, behavior: 'smooth'})}>
            Try IntentRoute
          </button>
        </div>
      </div>
    </section>
  );
};
