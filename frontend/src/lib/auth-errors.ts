const AUTH_ERRORS: Record<string, string> = {
  "Email not confirmed":
    "Veuillez confirmer votre email avant de vous connecter.",
  "Invalid login credentials": "Email ou mot de passe incorrect.",
  "User already registered": "Un compte existe déjà avec cet email.",
  "Password should be at least 6 characters":
    "Le mot de passe doit contenir au moins 6 caractères.",
  "Email rate limit exceeded":
    "Trop de tentatives. Veuillez réessayer plus tard.",
  "For security purposes, you can only request this once every 60 seconds":
    "Pour des raisons de sécurité, veuillez attendre 60 secondes entre chaque demande.",
  "New password should be different from the old password.":
    "Le nouveau mot de passe doit être différent de l'ancien.",
};

export function translateAuthError(message: string): string {
  return AUTH_ERRORS[message] || message;
}
