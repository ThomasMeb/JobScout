import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Politique de confidentialité",
  description: "Politique de confidentialité de JobScout : données collectées, traitements, droits RGPD et sécurité.",
  alternates: { canonical: "https://jobscout.mebarki.dev/legal/privacy" },
};

export default function PrivacyPage() {
  return (
    <>
      <h1>Politique de Confidentialité</h1>
      <p className="text-sm text-gray-500">Dernière mise à jour : février 2026</p>

      <h2>1. Responsable du traitement</h2>
      <p>
        Le responsable du traitement des données personnelles est Thomas Mebarki, développeur
        indépendant, joignable à{" "}
        <a href="mailto:thomas@mebarki.dev">thomas@mebarki.dev</a>.
      </p>

      <h2>2. Données collectées</h2>
      <p>Nous collectons les données suivantes :</p>
      <ul>
        <li><strong>Données de compte</strong> : adresse email, nom, mot de passe (hashé)</li>
        <li><strong>Données de profil</strong> : CV (texte), compétences, préférences d&apos;emploi, localisation souhaitée</li>
        <li><strong>Données d&apos;utilisation</strong> : interactions avec les offres (intéressé, rejeté, candidaté), scores IA</li>
        <li><strong>Données techniques</strong> : adresse IP, type de navigateur (pour la sécurité et le débogage)</li>
      </ul>

      <h2>3. Finalités du traitement</h2>
      <p>Vos données sont utilisées pour :</p>
      <ul>
        <li>Fournir le service de matching d&apos;offres d&apos;emploi personnalisé</li>
        <li>Générer des candidatures automatisées (CV, lettre de motivation)</li>
        <li>Envoyer des notifications (email, Telegram) sur les nouvelles offres correspondantes</li>
        <li>Améliorer la pertinence de l&apos;algorithme de scoring</li>
      </ul>

      <h2>4. Base légale</h2>
      <p>
        Le traitement est fondé sur l&apos;exécution du contrat (fourniture du service) et le
        consentement de l&apos;utilisateur pour les communications marketing.
      </p>

      <h2>5. Sous-traitants</h2>
      <p>Nous faisons appel aux sous-traitants suivants :</p>
      <ul>
        <li><strong>Supabase</strong> (hébergement base de données, authentification) — UE</li>
        <li><strong>Render</strong> (hébergement serveur) — UE (Frankfurt)</li>
        <li><strong>DeepSeek</strong> (intelligence artificielle pour le scoring et la génération)</li>
        <li><strong>Brevo</strong> (envoi d&apos;emails transactionnels) — France</li>
        <li><strong>Sentry</strong> (monitoring d&apos;erreurs)</li>
      </ul>

      <h2>6. Durée de conservation</h2>
      <ul>
        <li>Données de compte : conservées tant que le compte est actif</li>
        <li>Données de profil et CV : supprimées dans les 30 jours suivant la suppression du compte</li>
        <li>Offres d&apos;emploi scorées : conservées 90 jours</li>
        <li>Logs techniques : conservés 30 jours</li>
      </ul>

      <h2>7. Vos droits (RGPD)</h2>
      <p>
        Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des
        droits suivants :
      </p>
      <ul>
        <li><strong>Accès</strong> : obtenir une copie de vos données personnelles</li>
        <li><strong>Rectification</strong> : corriger des données inexactes</li>
        <li><strong>Suppression</strong> : demander l&apos;effacement de vos données</li>
        <li><strong>Portabilité</strong> : recevoir vos données dans un format structuré (CSV)</li>
        <li><strong>Opposition</strong> : vous opposer au traitement de vos données</li>
        <li><strong>Limitation</strong> : limiter le traitement dans certains cas</li>
      </ul>
      <p>
        Pour exercer ces droits, contactez-nous à{" "}
        <a href="mailto:thomas@mebarki.dev">thomas@mebarki.dev</a>. Nous répondrons dans un délai
        de 30 jours.
      </p>

      <h2>8. Sécurité</h2>
      <p>
        Nous mettons en œuvre des mesures techniques et organisationnelles pour protéger vos données :
        chiffrement en transit (HTTPS/TLS), authentification sécurisée (Supabase Auth), contrôle
        d&apos;accès par Row Level Security, et monitoring continu (Sentry).
      </p>

      <h2>9. Cookies</h2>
      <p>
        Le Service utilise uniquement des cookies techniques nécessaires à l&apos;authentification et
        au bon fonctionnement du site. Aucun cookie de tracking ou publicitaire n&apos;est utilisé.
      </p>

      <h2>10. Modifications</h2>
      <p>
        Cette politique peut être mise à jour. En cas de modification substantielle, les utilisateurs
        seront informés par email.
      </p>

      <h2>11. Contact</h2>
      <p>
        Pour toute question relative à vos données personnelles :{" "}
        <a href="mailto:thomas@mebarki.dev">thomas@mebarki.dev</a>
      </p>
      <p>
        Vous pouvez également adresser une réclamation à la CNIL :{" "}
        <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer">
          www.cnil.fr
        </a>
      </p>
    </>
  );
}
