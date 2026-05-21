import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecallScan",
  description: "External recall signals mapped to grocery catalog and inventory exposure.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
