import './globals.css';
import AppLayout from '@/components/AppLayout';

export const metadata = {
  title: 'EIOS — AI COO Platform',
  description: 'AI-Powered Business Operations Platform for Enterprise Intelligence and Safe Operational Execution',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
