export function SvgDefs() {
  return (
    <svg style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }} aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="sltGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#38220d" /><stop offset="0.22" stopColor="#8f6f3b" />
          <stop offset="0.45" stopColor="#c2a36b" /><stop offset="0.62" stopColor="#76582a" />
          <stop offset="0.82" stopColor="#b8985b" /><stop offset="1" stopColor="#2f1e0c" />
        </linearGradient>
        <linearGradient id="sltGoldV" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c2a36b" /><stop offset="0.45" stopColor="#8f6f3b" /><stop offset="1" stopColor="#3a250f" />
        </linearGradient>
        <filter id="sltGlow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.3" floodColor="#b89555" floodOpacity="0.22" />
          <feDropShadow dx="0" dy="1" stdDeviation="0.45" floodColor="#050302" floodOpacity="0.95" />
        </filter>
        <symbol id="sltCorner" viewBox="0 0 72 56">
          <g fill="none" stroke="#160d04" strokeWidth="3.2" strokeLinecap="square" strokeLinejoin="miter" opacity="0.95">
            <path d="M3 4.5H31M4.5 3V27"/><path d="M4.5 29V53M3 51.5H31"/>
            <rect x="6" y="6" width="20" height="20"/><rect x="10.5" y="10.5" width="11" height="11"/><rect x="14.5" y="14.5" width="3" height="3"/>
            <rect x="6" y="30" width="20" height="20"/><rect x="10.5" y="34.5" width="11" height="11"/><rect x="14.5" y="38.5" width="3" height="3"/>
            <path d="M28 5.5H70"/><path d="M28 50.5H70"/>
            <path d="M28 5.5V20.5H40.5V12.5H35.5V17"/><path d="M28 50.5V35.5H40.5V43.5H35.5V39"/>
            <path d="M33 25H54V19H48"/><path d="M33 31H54V37H48"/>
            <path d="M45 8.5C50 8.5 51.5 11 51.5 14C51.5 17 49.5 19 47 18.5C45 18 45.5 15 47.3 15.2" strokeLinecap="round"/>
            <path d="M45 47.5C50 47.5 51.5 45 51.5 42C51.5 39 49.5 37 47 37.5C45 38 45.5 41 47.3 40.8" strokeLinecap="round"/>
            <path d="M57 15V23M60 18H68"/><path d="M57 41V33M60 38H68"/>
          </g>
          <g fill="none" stroke="url(#sltGold)" strokeWidth="1.45" strokeLinecap="square" strokeLinejoin="miter" filter="url(#sltGlow)">
            <path d="M3 4.5H31M4.5 3V27"/><path d="M4.5 29V53M3 51.5H31"/>
            <rect x="6" y="6" width="20" height="20"/><rect x="10.5" y="10.5" width="11" height="11"/><rect x="14.5" y="14.5" width="3" height="3"/>
            <rect x="6" y="30" width="20" height="20"/><rect x="10.5" y="34.5" width="11" height="11"/><rect x="14.5" y="38.5" width="3" height="3"/>
            <path d="M28 5.5H70"/><path d="M28 50.5H70"/>
            <path d="M28 5.5V20.5H40.5V12.5H35.5V17"/><path d="M28 50.5V35.5H40.5V43.5H35.5V39"/>
            <path d="M33 25H54V19H48"/><path d="M33 31H54V37H48"/>
            <path d="M45 8.5C50 8.5 51.5 11 51.5 14C51.5 17 49.5 19 47 18.5C45 18 45.5 15 47.3 15.2" strokeLinecap="round"/>
            <path d="M45 47.5C50 47.5 51.5 45 51.5 42C51.5 39 49.5 37 47 37.5C45 38 45.5 41 47.3 40.8" strokeLinecap="round"/>
            <path d="M57 15V23M60 18H68"/><path d="M57 41V33M60 38H68"/>
          </g>
          <g fill="#b8985b" opacity="0.72" filter="url(#sltGlow)">
            <circle cx="39.5" cy="16.8" r="1.1"/><circle cx="39.5" cy="39.2" r="1.1"/>
            <circle cx="64.5" cy="22.6" r="0.9"/><circle cx="64.5" cy="33.4" r="0.9"/>
          </g>
        </symbol>
        <symbol id="sltIconAcademy" viewBox="0 0 32 32">
          <g transform="translate(0 1)" fill="#130c05" stroke="#130c05" strokeWidth="1.6" strokeLinejoin="round" opacity="0.96">
            <path d="M16 3.2 3.9 10.4h24.2L16 3.2Z"/>
            <rect x="5.2" y="11" width="21.6" height="2.2" rx="0.4"/>
            <rect x="7" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="12.2" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="17.4" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="22.6" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="5.2" y="23.4" width="21.6" height="2.4" rx="0.4"/>
            <rect x="3.6" y="26" width="24.8" height="2.7" rx="0.4"/>
          </g>
          <g transform="translate(0 1)" fill="url(#sltGoldV)" stroke="#4a3014" strokeWidth="0.55" strokeLinejoin="round" filter="url(#sltGlow)">
            <path d="M16 3.2 3.9 10.4h24.2L16 3.2Z"/>
            <rect x="5.2" y="11" width="21.6" height="2.2" rx="0.4"/>
            <rect x="7" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="12.2" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="17.4" y="13.4" width="3.3" height="10.1" rx="0.4"/><rect x="22.6" y="13.4" width="3.3" height="10.1" rx="0.4"/>
            <rect x="5.2" y="23.4" width="21.6" height="2.4" rx="0.4"/>
            <rect x="3.6" y="26" width="24.8" height="2.7" rx="0.4"/>
          </g>
        </symbol>
        <linearGradient id="slpGoldStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#37230e"/><stop offset="0.22" stopColor="#7f612e"/>
          <stop offset="0.46" stopColor="#b99a60"/><stop offset="0.66" stopColor="#6d5228"/>
          <stop offset="0.86" stopColor="#a9884c"/><stop offset="1" stopColor="#2b1b0a"/>
        </linearGradient>
        <linearGradient id="slpGoldFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c0a06a"/><stop offset="0.42" stopColor="#8b6c37"/><stop offset="1" stopColor="#33210d"/>
        </linearGradient>
        <filter id="slpGoldShadow" x="-40%" y="-40%" width="180%" height="180%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.26" floodColor="#b89555" floodOpacity="0.28"/>
          <feDropShadow dx="0" dy="1" stdDeviation="0.50" floodColor="#050302" floodOpacity="0.90"/>
        </filter>
        <symbol id="slpCorner" viewBox="0 0 32 32">
          <g fill="none" stroke="#120b04" strokeWidth="2.8" strokeLinecap="square" strokeLinejoin="miter" opacity="0.95">
            <path d="M2.6 29.4V2.6H29.4"/><path d="M6 26V6H26"/><path d="M10 22V10H22"/><path d="M14 18V14H18"/>
            <path d="M2.6 18H8.4M18 2.6V8.4"/><path d="M6 30H15M30 6V15"/>
          </g>
          <g fill="none" stroke="url(#slpGoldStroke)" strokeWidth="1.25" strokeLinecap="square" strokeLinejoin="miter" filter="url(#slpGoldShadow)">
            <path d="M2.6 29.4V2.6H29.4"/><path d="M6 26V6H26"/><path d="M10 22V10H22"/><path d="M14 18V14H18"/>
            <path d="M2.6 18H8.4M18 2.6V8.4"/><path d="M6 30H15M30 6V15"/>
          </g>
          <g fill="#b99a60" opacity="0.78" filter="url(#slpGoldShadow)">
            <circle cx="6" cy="6" r="1.1"/><circle cx="26" cy="6" r="1.1"/><circle cx="6" cy="26" r="1.1"/><circle cx="26" cy="26" r="1.1"/>
          </g>
        </symbol>
        <symbol id="slpTitleDivider" viewBox="0 0 320 12">
          <path d="M14 6H306" fill="none" stroke="#80683d" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M30 6H290" fill="none" stroke="#3d2c15" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M7 6l4-2.5 4 2.5-4 2.5-4-2.5ZM309 6l4-2.5 4 2.5-4 2.5-4-2.5Z" fill="#8d6f3b" stroke="#3a250f" strokeWidth="0.8" filter="url(#slpGoldShadow)"/>
        </symbol>
        <symbol id="slpCompass" viewBox="0 0 24 24">
          <g fill="#130c05" opacity="0.9"><path d="M12 2.6 14.6 9.4 21.4 12 14.6 14.6 12 21.4 9.4 14.6 2.6 12 9.4 9.4Z"/></g>
          <g fill="url(#slpGoldFill)" stroke="#4a3014" strokeWidth="0.5" filter="url(#slpGoldShadow)">
            <path d="M12 2.6 14.6 9.4 21.4 12 14.6 14.6 12 21.4 9.4 14.6 2.6 12 9.4 9.4Z"/>
          </g>
          <circle cx="12" cy="12" r="2.1" fill="#2c1c0b"/>
        </symbol>
        <symbol id="slpLock" viewBox="0 0 24 24">
          <path d="M7.25 10.2V8.15c0-2.95 2.07-5.1 4.75-5.1s4.75 2.15 4.75 5.1v2.05h1.2c.8 0 1.45.65 1.45 1.45v7.55c0 .8-.65 1.45-1.45 1.45H6.05c-.8 0-1.45-.65-1.45-1.45v-7.55c0-.8.65-1.45 1.45-1.45h1.2Zm2.3 0h4.9V8.15c0-1.62-.99-2.85-2.45-2.85S9.55 6.53 9.55 8.15v2.05Z" fill="#130c05" opacity="0.94"/>
          <path d="M7.25 10.2V8.15c0-2.95 2.07-5.1 4.75-5.1s4.75 2.15 4.75 5.1v2.05h1.2c.8 0 1.45.65 1.45 1.45v7.55c0 .8-.65 1.45-1.45 1.45H6.05c-.8 0-1.45-.65-1.45-1.45v-7.55c0-.8.65-1.45 1.45-1.45h1.2Zm2.3 0h4.9V8.15c0-1.62-.99-2.85-2.45-2.85S9.55 6.53 9.55 8.15v2.05Z" fill="url(#slpGoldFill)" stroke="#4a3014" strokeWidth="0.52" filter="url(#slpGoldShadow)"/>
          <circle cx="12" cy="15.2" r="1.25" fill="#2c1c0b" stroke="none" opacity="0.9"/>
          <path d="M12 16.1v2.2" stroke="#2c1c0b" strokeWidth="1" strokeLinecap="round"/>
        </symbol>
        <symbol id="slpChevron" viewBox="0 0 16 20">
          <path d="M4 3.2 12.4 10 4 16.8Z" fill="#170e05" opacity="0.94"/>
          <path d="M4 3.2 12.4 10 4 16.8Z" fill="url(#slpGoldFill)" stroke="#4a3014" strokeWidth="0.58" filter="url(#slpGoldShadow)"/>
        </symbol>
        <linearGradient id="srpGold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2f1f0d"/><stop offset="0.18" stopColor="#6a5028"/>
          <stop offset="0.42" stopColor="#b79b63"/><stop offset="0.58" stopColor="#7c5d2f"/>
          <stop offset="0.82" stopColor="#a98548"/><stop offset="1" stopColor="#2b1b0a"/>
        </linearGradient>
        <linearGradient id="srpBlue" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1d486b"/><stop offset="0.50" stopColor="#123455"/><stop offset="1" stopColor="#0b223a"/>
        </linearGradient>
        <filter id="srpGoldShadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="0" stdDeviation="0.28" floodColor="#b89555" floodOpacity="0.22"/>
          <feDropShadow dx="0" dy="1" stdDeviation="0.55" floodColor="#060302" floodOpacity="0.9"/>
        </filter>
        <symbol id="srpCorner" viewBox="0 0 42 42">
          <g fill="none" stroke="#150e06" strokeWidth="3" strokeLinecap="square" strokeLinejoin="miter" opacity="0.92">
            <path d="M5 37V5H37"/><path d="M10 33V10H33"/><path d="M15 29V15H29"/><path d="M20 25V20H25"/>
          </g>
          <g fill="none" stroke="url(#srpGold)" strokeWidth="1.35" strokeLinecap="square" strokeLinejoin="miter" filter="url(#srpGoldShadow)">
            <path d="M5 37V5H37"/><path d="M10 33V10H33" opacity="0.78"/>
            <path d="M15 29V15H29" opacity="0.62"/><path d="M20 25V20H25" opacity="0.82"/>
          </g>
          <circle cx="8" cy="34" r="1.5" fill="#9b7539"/>
        </symbol>
        <symbol id="srpDivider" viewBox="0 0 360 14">
          <path d="M22 7H338" fill="none" stroke="#80683d" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M38 7H322" fill="none" stroke="#3d2c15" strokeWidth="1" opacity="0.48" vectorEffect="non-scaling-stroke"/>
          <path d="M15 7l5-3 5 3-5 3-5-3ZM335 7l5-3 5 3-5 3-5-3Z" fill="#8d6f3b" stroke="#3a250f" strokeWidth="0.8" filter="url(#srpGoldShadow)"/>
        </symbol>
        <symbol id="srpInputFrame" viewBox="0 0 360 112">
          <path d="M14 3H346L357 14V98L346 109H14L3 98V14L14 3Z" fill="none" stroke="#2c2113" strokeWidth="3" vectorEffect="non-scaling-stroke" opacity="0.75"/>
          <path d="M15 4H345L356 15V97L345 108H15L4 97V15L15 4Z" fill="none" stroke="#837453" strokeWidth="1.4" vectorEffect="non-scaling-stroke" opacity="0.75"/>
          <path d="M19 8H341L352 19M8 19V93M19 104H341L352 93" fill="none" stroke="#ddd1aa" strokeWidth="0.7" vectorEffect="non-scaling-stroke" opacity="0.35"/>
        </symbol>
        <symbol id="srpSubmitFrame" viewBox="0 0 360 58">
          <path d="M16 4H344L356 16L348 54H12L4 16L16 4Z" fill="url(#srpBlue)" stroke="#111827" strokeWidth="2.6" vectorEffect="non-scaling-stroke"/>
          <path d="M18 7H342L352 17L345 51H15L8 17L18 7Z" fill="none" stroke="url(#srpGold)" strokeWidth="1.45" vectorEffect="non-scaling-stroke" filter="url(#srpGoldShadow)"/>
          <path d="M24 12H336L346 20L340 46H20L14 20L24 12Z" fill="none" stroke="#2e6792" strokeWidth="1" vectorEffect="non-scaling-stroke" opacity="0.9"/>
          <circle cx="16" cy="29" r="2.3" fill="#9a7538" stroke="#071827" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
          <circle cx="344" cy="29" r="2.3" fill="#9a7538" stroke="#071827" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
        </symbol>
      </defs>
    </svg>
  );
}

export function SlpCorners() {
  return (<>
    <svg className="slp-corner slp-corner--tl" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--tr" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--bl" aria-hidden="true"><use href="#slpCorner"/></svg>
    <svg className="slp-corner slp-corner--br" aria-hidden="true"><use href="#slpCorner"/></svg>
  </>);
}

export function SrpCorners() {
  return (<>
    <svg className="srp-corner srp-corner--tl" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--tr" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--bl" aria-hidden="true"><use href="#srpCorner"/></svg>
    <svg className="srp-corner srp-corner--br" aria-hidden="true"><use href="#srpCorner"/></svg>
  </>);
}

export function SsbBC({ cls }) {
  return (
    <svg className={cls} viewBox="0 0 17 17" fill="none" aria-hidden="true">
      <path d="M2 16V6Q2 2 6 2H16" stroke="#8d6f3b" strokeWidth="1.3"/>
      <path d="M7.5 7.5Q10.4 7.5 10.4 10.4" stroke="#8d6f3b" strokeWidth="1" opacity="0.85"/>
      <circle cx="7.4" cy="7.4" r="0.9" fill="#8d6f3b"/>
    </svg>
  );
}
