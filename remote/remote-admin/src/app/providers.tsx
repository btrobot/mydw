import { App as AntdApp, ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

import { AuthProvider } from '../features/auth/auth-context.js';
import { AppRouter } from '../routes/router.js';

export function AppProviders(): JSX.Element {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          colorBgLayout: '#f3f6fb',
          colorText: '#0f172a',
          borderRadius: 14,
          borderRadiusLG: 18,
        },
        components: {
          Layout: {
            bodyBg: '#f3f6fb',
            headerBg: '#ffffff',
            headerColor: '#0f172a',
            headerHeight: 80,
            headerPadding: '0 24px',
            siderBg: '#081523',
            triggerBg: '#0d2035',
            triggerColor: '#f8fafc',
          },
          Menu: {
            itemHeight: 62,
            itemBorderRadius: 14,
            subMenuItemBorderRadius: 14,
            itemMarginInline: 8,
            itemMarginBlock: 6,
            itemPaddingInline: 14,
            iconSize: 18,
            collapsedIconSize: 18,
            iconMarginInlineEnd: 12,
            activeBarHeight: 0,
            activeBarBorderWidth: 0,
            groupTitleFontSize: 11,
            darkItemBg: 'transparent',
            darkSubMenuItemBg: 'transparent',
            darkItemColor: 'rgba(226, 232, 240, 0.88)',
            darkItemHoverColor: '#ffffff',
            darkItemHoverBg: 'rgba(148, 163, 184, 0.12)',
            darkItemSelectedColor: '#ffffff',
            darkItemSelectedBg: 'rgba(22, 119, 255, 0.32)',
            darkGroupTitleColor: 'rgba(148, 163, 184, 0.72)',
          },
        },
      }}
    >
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
