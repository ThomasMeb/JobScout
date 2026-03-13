import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/dashboard", "/settings", "/auth", "/onboarding", "/update-password", "/forgot-password"],
    },
    sitemap: "https://jobscout.mebarki.dev/sitemap.xml",
  };
}
