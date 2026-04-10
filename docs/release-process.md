# Release Process (simple)

## 1. Planificar version
1. Crear milestone en GitHub: `vX.Y.Z`.
2. Mover issues objetivo al milestone.
3. Priorizar por impacto y riesgo.

## 2. Ejecutar trabajo
1. Una PR por issue (o por bloque coherente pequeno).
2. Titulo de PR claro y enlazado a issue.
3. Validar tests y smoke antes de merge.

## 3. Cerrar version
1. Actualizar `CHANGELOG.md`.
2. Verificar que todas las issues del milestone estan cerradas.
3. Crear tag/release en GitHub (`vX.Y.Z`) con notas del changelog.

## 4. Post-release
1. Abrir milestone siguiente (`vX.Y+1.0` o `vX.Y.Z+1`).
2. Pasar a `Unreleased` en `CHANGELOG.md` las mejoras siguientes.
3. Registrar incidencias detectadas en produccion como issues tipo bug.

