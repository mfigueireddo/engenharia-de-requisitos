/** Marca do BurguerJá: quadrado amarelo com as iniciais (tela 01). */
export function Logo({ tamanho = 88 }: { tamanho?: number }) {
  return (
    <div className="logo" style={{ width: tamanho, height: tamanho, fontSize: tamanho * 0.32 }} role="img" aria-label="BurguerJá">
      BJ
    </div>
  );
}
