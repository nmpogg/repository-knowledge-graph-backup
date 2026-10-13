import { createBrowserRouter, type RouteObject } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import DashboardPage from './routes/DashboardPage';
import OrdersPage from './routes/OrdersPage';
import OrderDetailPage from './routes/OrderDetailPage';
import OrderEditPage from './routes/OrderEditPage';
import NotFoundPage from './routes/NotFoundPage';
import CreateOrderPage from './routes/CreateOrderPage';

export const appRoutes: RouteObject[] = [
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'orders', element: <OrdersPage /> },
      { path: 'orders/:orderId', element: <OrderDetailPage /> },
      { path: 'orders/:orderId/edit', element: <OrderEditPage /> },
      { path: 'orders/new', element: <CreateOrderPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(appRoutes);
