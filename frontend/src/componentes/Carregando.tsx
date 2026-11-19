/** Indicador de carregamento. */
export function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="carregando" role="status">
      <span className="carregando__giro" aria-hidden />
      {texto}
    </div>
  );
}
