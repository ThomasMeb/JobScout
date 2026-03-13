import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Configuration du profil",
  robots: { index: false, follow: false },
};

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
