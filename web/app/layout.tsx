import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "BGC 3D | Explore Bonifacio Global City",
  description: "Explore Bonifacio Global City in 3D. Search named places, walk the streets, or follow a guided tour.",
  openGraph: {
    title: "BGC 3D",
    description: "Explore Bonifacio Global City in 3D.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
