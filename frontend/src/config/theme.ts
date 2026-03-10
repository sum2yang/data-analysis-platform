import type { ThemeConfig } from 'antd'

export const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      headerBg: '#fff',
      siderBg: '#fff',
      headerHeight: 56,
    },
    Menu: {
      itemBorderRadius: 6,
    },
  },
}
