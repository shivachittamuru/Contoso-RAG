import React from 'react';
import { RouteObject } from 'react-router-dom';
import MainLayout from '../layout/MainLayout';
import Default from '../views/Default';
import LoginPage from '../views/LoginPage';
import ProtectedRoute from '../security/ProtectedRoute';

console.log('entered MainRoutes.tsx');
const MainRoutes: RouteObject[] = [
    {
      path: '/',
      element: <MainLayout />,
      children: [
        {
          index: true,
          element: <ProtectedRoute component={Default} />,
        }
      ],
    },
    {
        path: '/app',
        element: <MainLayout />,
        children: [
          {
            index: true,
            element: <ProtectedRoute component={Default} />,
          }
        ],
      },
    {
      path: 'login',
      element: <LoginPage />,
    },
  ];
  console.log('MainRoutes: ', MainRoutes);
  console.log('MainRoutes[0].children: ', MainRoutes[0].children);
  console.log('exporting MainRoutes');
  export default MainRoutes;