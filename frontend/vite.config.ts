import { defineConfig } from 'vite';

export default defineConfig({
    server: { port: 3000, strictPort: true },
    build: {
        assetsDir: 'static',
        rollupOptions: { input: ['index.html', 'chat-bot.html'] },
    },
});
