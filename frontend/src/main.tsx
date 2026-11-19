import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./estilos/tema.css";
import "./estilos/global.css";
import "./componentes/componentes.css";
import "./paginas/paginas.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
