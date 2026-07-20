export function ScreenShell({ className = "", backgroundContent = null, topBar, children }) {
  const shellClassName = ["app-bg", className].filter(Boolean).join(" ");

  return (
    <div style={{ background: "#050504" }}>
      <div className={shellClassName}>
        <div className="app-bg-overlay"/>
        {backgroundContent}
        <div className="app-frame">
          {topBar}
          {children}
        </div>
      </div>
    </div>
  );
}
