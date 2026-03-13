export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "JobScout",
    url: "https://jobscout.mebarki.dev",
    logo: "https://jobscout.mebarki.dev/logo.svg",
    description:
      "Matching d'offres d'emploi par IA. Scraping multi-sources, scoring intelligent et candidature automatisée.",
    founder: {
      "@type": "Person",
      name: "Thomas Mebarki",
    },
    contactPoint: {
      "@type": "ContactPoint",
      email: "thomas@mebarki.dev",
      contactType: "customer support",
      availableLanguage: "French",
    },
  };
}

export function softwareApplicationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "JobScout",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: "https://jobscout.mebarki.dev",
    description:
      "Plateforme de matching d'offres d'emploi par intelligence artificielle. Scraping de 10+ sites, scoring IA personnalisé et candidature automatique.",
    offers: [
      {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
        name: "Gratuit",
        description: "10 offres évaluées par cycle, tableau de bord, export CSV",
      },
      {
        "@type": "Offer",
        price: "9",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "UnitPriceSpecification",
          price: "9",
          priceCurrency: "USD",
          billingDuration: "P1M",
        },
        name: "Pro",
        description:
          "Scoring illimité, alertes Telegram, candidature automatique, recherche entreprise IA",
      },
    ],
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: "4.8",
      ratingCount: "50",
      bestRating: "5",
    },
  };
}

export function faqJsonLd(
  faqs: { question: string; answer: string }[]
) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}
