import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  // MUHIM: frontend ham backend/bot bilan BIR XIL ".env" faylidan
  // (loyihaning ROOT papkasidan) o'qiydi - alohida frontend/.env yaratish
  // shart emas, hammasi bitta joyda boshqariladi.
  envDir: path.resolve(__dirname, '..'),
  server: {
    port: 5173,
  },
});
