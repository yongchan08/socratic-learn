import { ShieldCheck } from "lucide-react";
import { ScreenShell } from "../components/ScreenShell.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function AdminLoginView({
  audioSettings,
  adminPassword,
  adminError,
  onPasswordChange,
  onSubmit,
}) {
  return (
    <ScreenShell
      className="library-bg admin-login-bg"
      topBar={<TopBar audioSettings={audioSettings}/>}
    >
      <main className="admin-login-shell">
        <section className="admin-login-card" aria-labelledby="admin-login-title">
          <ShieldCheck className="admin-login-icon" size={34}/>
          <span className="admin-login-eyebrow">관리자 전용</span>
          <h1 id="admin-login-title">학습 로드맵 관리</h1>
          <p>로드맵을 생성하고 관리하려면 관리자 비밀번호를 입력하세요.</p>
          <form onSubmit={onSubmit}>
            <label htmlFor="admin-password">관리자 비밀번호</label>
            <input
              id="admin-password"
              type="password"
              inputMode="numeric"
              autoComplete="current-password"
              autoFocus
              value={adminPassword}
              onChange={onPasswordChange}
              aria-invalid={Boolean(adminError)}
              aria-describedby={adminError ? "admin-password-error" : undefined}
            />
            {adminError && <p id="admin-password-error" className="admin-login-error" role="alert">{adminError}</p>}
            <button type="submit" disabled={!adminPassword}>입장하기</button>
          </form>
        </section>
      </main>
    </ScreenShell>
  );
}
