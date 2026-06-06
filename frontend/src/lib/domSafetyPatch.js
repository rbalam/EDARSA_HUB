/**
 * domSafetyPatch.js - EDARSAHUB
 *
 * Mitigación para el crash de React `NotFoundError: Failed to execute 'removeChild'
 * on 'Node'` (y su variante en `insertBefore`) que se dispara cuando la TRADUCCIÓN
 * AUTOMÁTICA del navegador (Chrome / Safari Translate) reescribe los nodos de texto
 * de la página. Al modificar el DOM por fuera de React, la reconciliación intenta
 * remover/insertar nodos que ya cambiaron de padre y lanza el error, dejando la app
 * en pantalla en blanco / overlay de error en tiempo de ejecución.
 *
 * Referencia: facebook/react#11538
 *
 * Este parche debe importarse ANTES de montar React (ver index.js).
 */
if (typeof Node === "function" && Node.prototype) {
  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function (child) {
    if (child.parentNode !== this) {
      if (typeof console !== "undefined") {
        console.warn(
          "[domSafetyPatch] removeChild omitido: el nodo no pertenece a este padre (probable traducción del navegador).",
          child
        );
      }
      return child;
    }
    return originalRemoveChild.apply(this, arguments);
  };

  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function (newNode, referenceNode) {
    if (referenceNode && referenceNode.parentNode !== this) {
      if (typeof console !== "undefined") {
        console.warn(
          "[domSafetyPatch] insertBefore: nodo de referencia con padre distinto, se agrega al final.",
          referenceNode
        );
      }
      return originalInsertBefore.call(this, newNode, null);
    }
    return originalInsertBefore.apply(this, arguments);
  };
}
