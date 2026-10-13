import { NavLink, Outlet } from 'react-router-dom';

export default function RootLayout() {
  return (
    <>
      <header>
        <strong>Order Operations Console</strong>
        <nav aria-label="Main navigation">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/orders">Orders</NavLink>
          <NavLink to="/admin/users">Admin</NavLink>
        </nav>
      </header>
      <main><Outlet /></main>
    </>
  );
}
