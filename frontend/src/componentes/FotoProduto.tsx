/** Espaço reservado para a foto (o SGL simulado não envia imagens). */
export function FotoProduto({ nome, tamanho = "md" }: { nome: string; tamanho?: "sm" | "md" | "lg" }) {
  const inicial = nome.trim().charAt(0).toUpperCase();
  return (
    <div className={`foto foto--${tamanho}`} role="img" aria-label={`Foto de ${nome}`}>
      <span>{tamanho === "sm" ? inicial : "foto"}</span>
    </div>
  );
}
