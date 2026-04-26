import type { ThemeConfig } from 'antd';
import type { CSSProperties } from 'react';

export const ADMIN_SHELL_DIMENSIONS = {
  siderWidth: 280,
  siderCollapsedWidth: 88,
  siderOuterPadding: '16px 16px 24px',
  contentPadding: 28,
  headerPadding: '0 24px',
  menuItemHeight: 56,
  menuItemRadius: 14,
  menuGroupTitleSize: 11,
  navIconSize: 30,
  navGlyphSize: 11,
} as const;

export const ADMIN_SHELL_COLORS = {
  primary: '#1677ff',
  text: '#0f172a',
  layoutBg: '#f3f6fb',
  containerBg: '#ffffff',
  siderBg: '#081523',
  siderTriggerBg: '#0d2035',
  siderTriggerText: '#f8fafc',
  siderTextStrong: '#f8fafc',
  siderTextMuted: 'rgba(226, 232, 240, 0.72)',
  siderTextDefault: 'rgba(226, 232, 240, 0.88)',
  siderGroupTitle: 'rgba(148, 163, 184, 0.72)',
  siderHoverBg: 'rgba(148, 163, 184, 0.12)',
  siderSelectedBg: 'rgba(22, 119, 255, 0.32)',
  siderPanelBg: 'rgba(15, 23, 42, 0.56)',
  siderPanelSoftBg: 'rgba(15, 23, 42, 0.5)',
  siderPanelBorder: 'rgba(148, 163, 184, 0.16)',
  siderBorder: 'rgba(148, 163, 184, 0.14)',
  siderInsetLine: 'rgba(255, 255, 255, 0.04)',
  brandAccent: '#7dd3fc',
  brandGradient: 'linear-gradient(135deg, #38bdf8, #2563eb)',
  navGlyphGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.92), rgba(37, 99, 235, 0.78))',
  navGlyphText: '#eff6ff',
  collapsedOperatorBg: 'rgba(59, 130, 246, 0.22)',
  collapsedOperatorText: '#bfdbfe',
  headerBorder: 'rgba(148, 163, 184, 0.16)',
  headerPanelBg: 'rgba(248, 250, 252, 0.96)',
  topHighlight:
    'radial-gradient(circle at top, rgba(37, 99, 235, 0.22), transparent 34%), linear-gradient(180deg, rgba(8, 21, 35, 1), rgba(10, 25, 41, 1))',
} as const;

export const adminTheme: ThemeConfig = {
  token: {
    colorPrimary: ADMIN_SHELL_COLORS.primary,
    colorBgLayout: ADMIN_SHELL_COLORS.layoutBg,
    colorText: ADMIN_SHELL_COLORS.text,
    borderRadius: 14,
    borderRadiusLG: 18,
  },
  components: {
    Layout: {
      bodyBg: ADMIN_SHELL_COLORS.layoutBg,
      headerBg: ADMIN_SHELL_COLORS.containerBg,
      headerColor: ADMIN_SHELL_COLORS.text,
      headerHeight: 80,
      headerPadding: ADMIN_SHELL_DIMENSIONS.headerPadding,
      siderBg: ADMIN_SHELL_COLORS.siderBg,
      triggerBg: ADMIN_SHELL_COLORS.siderTriggerBg,
      triggerColor: ADMIN_SHELL_COLORS.siderTriggerText,
    },
    Menu: {
      itemHeight: ADMIN_SHELL_DIMENSIONS.menuItemHeight,
      itemBorderRadius: ADMIN_SHELL_DIMENSIONS.menuItemRadius,
      subMenuItemBorderRadius: ADMIN_SHELL_DIMENSIONS.menuItemRadius,
      itemMarginInline: 8,
      itemMarginBlock: 4,
      itemPaddingInline: 14,
      iconSize: 18,
      collapsedIconSize: 18,
      iconMarginInlineEnd: 12,
      activeBarHeight: 0,
      activeBarBorderWidth: 0,
      groupTitleFontSize: ADMIN_SHELL_DIMENSIONS.menuGroupTitleSize,
      darkItemBg: 'transparent',
      darkSubMenuItemBg: 'transparent',
      darkItemColor: ADMIN_SHELL_COLORS.siderTextDefault,
      darkItemHoverColor: '#ffffff',
      darkItemHoverBg: ADMIN_SHELL_COLORS.siderHoverBg,
      darkItemSelectedColor: '#ffffff',
      darkItemSelectedBg: ADMIN_SHELL_COLORS.siderSelectedBg,
      darkGroupTitleColor: ADMIN_SHELL_COLORS.siderGroupTitle,
    },
  },
};

export function createShellCardStyle(borderRadius: number, background: string): CSSProperties {
  return {
    borderRadius,
    border: `1px solid ${ADMIN_SHELL_COLORS.siderPanelBorder}`,
    background,
  };
}

export function createSidebarContainerStyle(): CSSProperties {
  return {
    display: 'flex',
    minHeight: '100%',
    flexDirection: 'column',
    gap: 12,
    padding: ADMIN_SHELL_DIMENSIONS.siderOuterPadding,
    background: ADMIN_SHELL_COLORS.topHighlight,
  };
}
