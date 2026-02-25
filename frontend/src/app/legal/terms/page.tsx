export const metadata = {
  title: "Conditions Générales d'Utilisation — JobScout",
};

export default function TermsPage() {
  return (
    <>
      <h1>Conditions Générales d&apos;Utilisation</h1>
      <p className="text-sm text-gray-500">Dernière mise à jour : février 2026</p>

      <h2>1. Objet</h2>
      <p>
        Les présentes Conditions Générales d&apos;Utilisation (CGU) régissent l&apos;accès et
        l&apos;utilisation de la plateforme JobScout, accessible à l&apos;adresse{" "}
        <strong>jobscout.mebarki.dev</strong> (ci-après « le Service »).
      </p>

      <h2>2. Acceptation des CGU</h2>
      <p>
        En créant un compte ou en utilisant le Service, l&apos;utilisateur accepte sans réserve les
        présentes CGU. Si vous n&apos;acceptez pas ces conditions, veuillez ne pas utiliser le Service.
      </p>

      <h2>3. Description du Service</h2>
      <p>
        JobScout est un service de veille emploi automatisée qui collecte des offres d&apos;emploi
        depuis des sources publiques, les analyse par intelligence artificielle et les présente à
        l&apos;utilisateur selon son profil. Le Service inclut également des fonctionnalités de
        préparation de candidature automatisée.
      </p>

      <h2>4. Inscription et compte</h2>
      <p>
        L&apos;inscription est gratuite. L&apos;utilisateur s&apos;engage à fournir des informations
        exactes et à maintenir la confidentialité de ses identifiants de connexion. Toute activité
        réalisée via son compte est sous sa responsabilité.
      </p>

      <h2>5. Plans et tarification</h2>
      <p>
        Le Service propose un plan gratuit et un plan payant (Pro). Les fonctionnalités et limites de
        chaque plan sont décrites sur la page Pricing. Les prix peuvent être modifiés avec un préavis
        de 30 jours.
      </p>

      <h2>6. Utilisation acceptable</h2>
      <p>L&apos;utilisateur s&apos;engage à ne pas :</p>
      <ul>
        <li>Utiliser le Service à des fins illicites ou non autorisées</li>
        <li>Tenter de contourner les limites techniques du Service</li>
        <li>Revendre ou redistribuer les données collectées par le Service</li>
        <li>Utiliser des systèmes automatisés pour accéder au Service en dehors de l&apos;API fournie</li>
      </ul>

      <h2>7. Propriété intellectuelle</h2>
      <p>
        Le code source, le design et le contenu du Service sont la propriété de JobScout. Les offres
        d&apos;emploi collectées restent la propriété de leurs éditeurs respectifs.
      </p>

      <h2>8. Limitation de responsabilité</h2>
      <p>
        Le Service est fourni « en l&apos;état ». JobScout ne garantit pas l&apos;exactitude des
        offres d&apos;emploi collectées ni des scores attribués par l&apos;IA. L&apos;utilisateur
        reste seul responsable de ses candidatures.
      </p>

      <h2>9. Résiliation</h2>
      <p>
        L&apos;utilisateur peut supprimer son compte à tout moment depuis les paramètres. JobScout
        se réserve le droit de suspendre un compte en cas de violation des présentes CGU.
      </p>

      <h2>10. Droit applicable</h2>
      <p>
        Les présentes CGU sont régies par le droit français. Tout litige sera soumis aux tribunaux
        compétents de Paris.
      </p>

      <h2>11. Contact</h2>
      <p>
        Pour toute question relative aux présentes CGU :{" "}
        <a href="mailto:thomas@mebarki.dev">thomas@mebarki.dev</a>
      </p>
    </>
  );
}
