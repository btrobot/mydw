import { App as AntdApp, ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

import { AuthProvider } from '../features/auth/auth-context.js';
import { AppRouter } from '../routes/router.js';

export function AppProviders(): JSX.Element {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <ConfigProvider>
      <AntdApp>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AppRouter />
          </AuthProvider>
        </QueryClientProvider>
      </AntdApp>
    </ConfigProvider>
  );
}
