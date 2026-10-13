import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { getEnvironment } from '@/config/environment';

export default function AdminLayout() {
  const location = useLocation();
  if (!getEnvironment().enableAdmin) {
    return <Navigate to="/" replace state={{ deniedFrom: location.pathname }} />;
  }
  return <section aria-label="Administration"><Outlet /></section>;
}
