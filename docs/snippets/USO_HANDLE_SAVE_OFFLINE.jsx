// =============================================================================
// SNIPPET: USO DE handleSaveOffline EN COMPONENTES
// OBJETIVO: Ejemplo de integración de la utilidad offline-first
// =============================================================================

import { handleSaveOffline } from '@/lib/handleSaveOffline';

// Dentro de tu componente:
const handleSave = async (data, endpoint) => {
  setIsLoading(true);
  await handleSaveOffline(data, endpoint, onClose);
  setIsLoading(false);
};

// ─────────────────────────────────────────────────────────────────────────────
// EJEMPLO EN UserForm.jsx
// ─────────────────────────────────────────────────────────────────────────────
const UserForm = ({ onClose }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const onSubmit = async (userData) => {
    setIsLoading(true);
    await handleSaveOffline(userData, '/usuarios/guardar', onClose);
    setIsLoading(false);
  };
  
  // ... resto del componente
};

// ─────────────────────────────────────────────────────────────────────────────
// EJEMPLO EN RoleForm.jsx
// ─────────────────────────────────────────────────────────────────────────────
const RoleForm = ({ onClose }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const onSubmit = async (rolData) => {
    setIsLoading(true);
    await handleSaveOffline(rolData, '/roles/guardar', onClose);
    setIsLoading(false);
  };
  
  // ... resto del componente
};
