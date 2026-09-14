import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useCurrentUser, useLogout } from "../api/auth";
import { useAckWhatsNew, useWhatsNew } from "../api/whatsNew";
import logo from "../assets/logo.png";
import ChangePasswordForm from "./ChangePasswordForm";
import LanguageSwitcher from "./LanguageSwitcher";
import WhatsNewModal from "./WhatsNewModal";

function Layout() {
  const { t } = useTranslation();
  const { data } = useCurrentUser();
  const logout = useLogout();
  const mustChangePassword = data?.authenticated && data.user.must_change_password;

  // Same gate as the dialog itself: the endpoint is
  // IsAuthenticatedAndPasswordCurrent, so querying it any earlier than this
  // would 403 on every login-screen/forced-password-change load.
  const whatsNewEnabled = Boolean(data?.authenticated && !mustChangePassword);
  const { data: whatsNew } = useWhatsNew(whatsNewEnabled);
  const ackWhatsNew = useAckWhatsNew();
  const [manuallyOpened, setManuallyOpened] = useState(false);
  // Locally authoritative once dismissed this session: the ack is fire-and-
  // forget, so if it's slow or fails, `whatsNew.unseen` staying true must not
  // pop the dialog straight back open the instant it's closed. Deriving
  // visibility during render (rather than syncing it into state via an
  // effect) also means there's nothing to reconcile once the query resolves.
  //
  // Keyed by user id, not a plain boolean: Layout is the route layout
  // element and never unmounts on login/logout (see DESIGN.md's "New-loan
  // draft persistence" for the same class of bug), so a bare `dismissed`
  // flag set by one user would silently suppress the dialog for the next
  // user who logs in on the same tab.
  const userId = data?.authenticated ? data.user.id : null;
  const [dismissedFor, setDismissedFor] = useState(null);
  const whatsNewOpen = manuallyOpened || (Boolean(whatsNew?.unseen) && dismissedFor !== userId);

  const closeWhatsNew = () => {
    setManuallyOpened(false);
    setDismissedFor(userId);
    ackWhatsNew.mutate();
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
        <div className="container-fluid">
          <div className="d-flex align-items-center">
            <NavLink className="navbar-brand d-flex align-items-center gap-2" to="/">
              <img
                src={logo}
                height="40"
                alt="Karhunvartijat ry"
                className="bg-white rounded px-2 py-1"
              />
            </NavLink>
            {/* Outside the collapse so a user can switch language (needed most
                acutely on the logged-out login screen) without first opening
                the hamburger menu on a tablet-width viewport. */}
            <LanguageSwitcher />
          </div>
          {data?.authenticated ? (
            <button
              className="navbar-toggler"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#nav-content"
              aria-controls="nav-content"
              aria-expanded="false"
              aria-label={t("layout.toggleNav")}
            >
              <span className="navbar-toggler-icon" />
            </button>
          ) : null}
          <div className="collapse navbar-collapse" id="nav-content">
            <ul className="navbar-nav me-auto">
              {data?.authenticated ? (
                <li className="nav-item">
                  <NavLink className="nav-link" to="/storage">
                    {t("layout.storage")}
                  </NavLink>
                </li>
              ) : null}
              {data?.authenticated ? (
                <li className="nav-item">
                  <NavLink className="nav-link" to="/loans" end>
                    {t("layout.loans")}
                  </NavLink>
                </li>
              ) : null}
              {data?.authenticated ? (
                <li className="nav-item">
                  <NavLink className="nav-link" to="/loans/archive">
                    {t("layout.archive")}
                  </NavLink>
                </li>
              ) : null}
              {data?.authenticated ? (
                <li className="nav-item">
                  <NavLink className="nav-link" to="/repairs">
                    {t("layout.repairs")}
                  </NavLink>
                </li>
              ) : null}
            </ul>
            {data?.authenticated ? (
              <div className="d-flex align-items-center gap-2">
                <span className="text-light small">{data.user.username}</span>
                {!mustChangePassword ? (
                  <button
                    className="btn btn-sm btn-outline-light"
                    type="button"
                    onClick={() => setManuallyOpened(true)}
                  >
                    What&apos;s new
                  </button>
                ) : null}
                <NavLink className="btn btn-sm btn-outline-light" to="/account/profile">
                  {t("layout.profile")}
                </NavLink>
                <NavLink className="btn btn-sm btn-outline-light" to="/account/password">
                  {t("layout.changePassword")}
                </NavLink>
                <button
                  className="btn btn-sm btn-outline-light"
                  type="button"
                  onClick={() => logout.mutate()}
                  disabled={logout.isPending}
                >
                  {t("layout.logout")}
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </nav>
      <main className="container-fluid flex-grow-1 py-3">
        {mustChangePassword ? <ChangePasswordForm forced /> : <Outlet />}
      </main>
      {!mustChangePassword && whatsNewOpen ? (
        <WhatsNewModal entries={whatsNew?.entries} onClose={closeWhatsNew} />
      ) : null}
    </div>
  );
}

export default Layout;
