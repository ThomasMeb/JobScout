export const metadata = {
  title: "Mentions Légales — JobScout",
};

export default function MentionsPage() {
  return (
    <>
      <h1>Mentions Légales</h1>
      <p className="text-sm text-gray-500">Dernière mise à jour : février 2026</p>

      <h2>Éditeur du site</h2>
      <p>
        <strong>Thomas Mebarki</strong>
        <br />
        Développeur indépendant
        <br />
        Email : <a href="mailto:thomas@mebarki.dev">thomas@mebarki.dev</a>
      </p>

      <h2>Hébergement</h2>
      <p>
        <strong>Render Services, Inc.</strong>
        <br />
        525 Brannan Street, Suite 300
        <br />
        San Francisco, CA 94107, USA
        <br />
        Site web : <a href="https://render.com" target="_blank" rel="noopener noreferrer">render.com</a>
      </p>
      <p>
        Région d&apos;hébergement : <strong>Frankfurt, Allemagne (UE)</strong>
      </p>

      <h2>Base de données</h2>
      <p>
        <strong>Supabase Inc.</strong>
        <br />
        970 Toa Payoh North, Singapore 318992
        <br />
        Site web : <a href="https://supabase.com" target="_blank" rel="noopener noreferrer">supabase.com</a>
      </p>

      <h2>Propriété intellectuelle</h2>
      <p>
        L&apos;ensemble du contenu du site (textes, graphismes, logiciels, code source) est protégé
        par le droit de la propriété intellectuelle. Toute reproduction non autorisée est interdite.
      </p>

      <h2>Données personnelles</h2>
      <p>
        Pour toute information relative au traitement de vos données personnelles, veuillez
        consulter notre{" "}
        <a href="/legal/privacy">Politique de Confidentialité</a>.
      </p>
    </>
  );
}
