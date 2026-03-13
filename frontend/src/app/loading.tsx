export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0">
      <div className="text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-amber border-t-transparent" />
        <p className="mt-4 text-sm text-text-muted">Chargement...</p>
      </div>
    </div>
  );
}
