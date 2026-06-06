// Función para obtener productos dinámicamente
const fetchProductos = async (page = 1, incluirInactivos = false) => {
  try {
    // 1. Construimos los parámetros base obligatorios (paginación)
    const params = new URLSearchParams({
      page: page,
      page_size: 20
    });

    // 2. Evaluamos el estado del checkbox para filtrar en la Base de Datos
    // Si NO queremos incluir inactivos, pedimos solo los activos al servidor
    if (!incluirInactivos) {
      params.append('status', 'active'); 
    }

    // 3. Ejecutamos la petición con los parámetros concatenados
    // Ejemplo resultante: api/costos-margenes/productos?page=1&page_size=20&status=active
    const response = await axios.get(`api/costos-margenes/productos?${params.toString()}`);
    
    // 4. Actualizamos el estado de la tabla con los datos reales
    setDatos(response.data.productos);

  } catch (error) {
    console.error("Error al cargar productos:", error);
  }
};

// Estado local para controlar el valor visual del checkbox (React useState)
const [incluirInactivos, setIncluirInactivos] = useState(false);

// ... en tu renderizado (return) ...

<input 
  type="checkbox" 
  id="filtro-inactivos"
  checked={incluirInactivos}
  onChange={(e) => {
    const isChecked = e.target.checked;
    // 1. Actualizamos el checkbox en la pantalla
    setIncluirInactivos(isChecked); 
    // 2. Forzamos a la API a traer la página 1 con la nueva regla
    fetchProductos(1, isChecked);   
  }} 
/>
<label htmlFor="filtro-inactivos">Incluir inactivos/baja</label>
