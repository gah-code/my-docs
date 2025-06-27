import { defineConfig } from 'vitepress';

export default {
  title: 'My Docs',
  description: 'A simple documentation site using VitePress',
  themeConfig: {
    sidebar: [
      {
        text: 'Guide',
        items: [{ text: 'Getting Started', link: '/guide' }],
      },
      {
        text: 'Unified Audit',
        items: [{ text: 'Draft', link: '/draft' }],
      },
      {
        text: 'Unified Audit Table',
        items: [{ text: 'Table', link: '/table' }],
      },
    ],
  },
};
