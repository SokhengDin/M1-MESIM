import "./globals.css";

export const metadata = {
  title: "MESIM · Quadratic Equation Trainer",
  description: "ENSIIE project — simulate and solve quadratic equations",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning style={{ height: "100%", margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
