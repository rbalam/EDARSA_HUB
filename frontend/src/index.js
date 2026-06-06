import "@/lib/domSafetyPatch";
import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import HostRouter from "@/HostRouter";

/**
 * Punto de entrada principal - EDARSAHUB
 * 
 * Utiliza HostRouter para enrutamiento basado en subdominio:
 * - inteligencia.edarsa.com.mx → Portal Inteligencia Comercial IA
 * - proveedores.edarsa.com.mx  → Portal de Proveedores
 * - Cualquier otro dominio     → CRM Principal
 */
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <HostRouter />
  </React.StrictMode>,
);
