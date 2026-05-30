import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HireIQ",
  description: "Placement preparation workspace for candidates.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
