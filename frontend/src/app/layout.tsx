import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://jobscout.mebarki.dev"),
  title: {
    default: "JobScout — Matching emploi par IA",
    template: "%s | JobScout",
  },
  description:
    "Scraping multi-sources, scoring IA personnalisé et candidature automatique. Trouvez votre prochain poste sans effort.",
  keywords: [
    "recherche emploi",
    "matching IA",
    "offres emploi",
    "scoring CV",
    "candidature automatique",
    "scraping emploi",
    "JobScout",
  ],
  authors: [{ name: "Thomas Mebarki" }],
  creator: "Thomas Mebarki",
  icons: { icon: "/logo.svg" },
  openGraph: {
    type: "website",
    locale: "fr_FR",
    url: "https://jobscout.mebarki.dev",
    siteName: "JobScout",
    title: "JobScout — Matching emploi par IA",
    description:
      "Scraping multi-sources, scoring IA personnalisé et candidature automatique.",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "JobScout" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "JobScout — Matching emploi par IA",
    description:
      "Scraping multi-sources, scoring IA personnalisé et candidature automatique.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
