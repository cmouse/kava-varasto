import { NavLink, Outlet } from "react-router-dom";

import { useCurrentUser, useLogout } from "../api/auth";
import LanguageSwitcher from "./LanguageSwitcher";

function Layout() {
  const { data } = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="d-flex flex-column min-vh-100">
      <nav className="navbar navbar-expand-md navbar-dark bg-dark">
        <div className="container-fluid">
          <NavLink className="navbar-brand" to="/">
            Kava-varasto
          </NavLink>
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#nav-content"
            aria-controls="nav-content"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon" />
          </button>
          <div className="collapse navbar-collapse" id="nav-content">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <NavLink className="nav-link" to="/" end>
                  Home
                </NavLink>
              </li>
            </ul>
            <div className="d-flex align-items-center gap-3">
              <LanguageSwitcher />
              {data?.authenticated ? (
                <div className="d-flex align-items-center gap-2">
                  <span className="text-light small">{data.user.username}</span>
                  <button
                    className="btn btn-sm btn-outline-light"
                    type="button"
                    onClick={() => logout.mutate()}
                    disabled={logout.isPending}
                  >
                    Log out
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </nav>
      <main className="container-fluid flex-grow-1 py-3">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
