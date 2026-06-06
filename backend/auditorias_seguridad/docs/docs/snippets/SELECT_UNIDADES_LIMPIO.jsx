// =============================================================================
// SNIPPET: SELECT LIMPIO DE UNIDADES DE NEGOCIO (SIN SPAN EN OPTION)
// OBJETIVO: Evitar errores de hidratación por HTML inválido
// =============================================================================

// Sustituye el bloque del <select> actual por este código limpio:
<select 
  className="w-full h-10 border rounded-md px-3" 
  data-testid="unidad-negocio" 
  value={value} 
  onChange={onChange}
>
  {unidadesNegocio.map((unidad) => (
    <option 
      key={unidad.id} 
      value={unidad.id}
    >
      {unidad.nombre}
    </option>
  ))}
</select>

// IMPORTANTE: 
// - NO usar <span> dentro de <option>
// - El texto debe ir DIRECTO dentro del <option>
// - Esto previene: "Hydration failed because the server rendered HTML didn't match the client"
