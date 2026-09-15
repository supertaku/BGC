import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Interactive BGC City Model",
  description: "Explore geographically grounded BGC massing, detailed landmarks, and mapped street context.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
