import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'Pulso — Inteligência de conteúdo', description: 'Transforme sinais em ideias originais.' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
