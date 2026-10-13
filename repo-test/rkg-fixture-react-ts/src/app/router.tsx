import { createBrowserRouter, type RouteObject } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import AdminLayout from './layouts/AdminLayout';
import DashboardPage from './routes/DashboardPage';
import OrdersPage from './routes/OrdersPage';
import OrderDetailPage from './routes/OrderDetailPage';
import OrderEditPage from './routes/OrderEditPage';
import AdminUsersPage from './routes/AdminUsersPage';
import NotFoundPage from './routes/NotFoundPage';
import { ADMIN_USERS_PATH } from '../analysis-cases/positive/importedConstants';

export const appRoutes: RouteObject[] = [
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'orders', element: <OrdersPage /> },
      { path: 'orders/:orderId', element: <OrderDetailPage /> },
      { path: 'orders/:orderId/edit', element: <OrderEditPage /> },
      { element: <AdminLayout />, children: [{ path: ADMIN_USERS_PATH, element: <AdminUsersPage /> }] },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(appRoutes);
