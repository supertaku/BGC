import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BGC 3D Pipeline Viewer",
  description: "Synthetic Blender-to-Three.js integration fixture",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
