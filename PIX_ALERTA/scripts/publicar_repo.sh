#!/usr/bin/env bash
# Publica PIX_ALERTA al repositorio de despliegue.
#
#   bash PIX_ALERTA/scripts/publicar_repo.sh        (desde la raiz del workspace)
#
# POR QUE SUBTREE Y NO UNA COPIA
# ------------------------------
# El codigo vive en UN solo lugar: el workspace. `git subtree split` genera una rama con
# PIX_ALERTA en la raiz y su historial, y esa rama se empuja al repo de la nube. No hay
# dos copias que editar ni que se puedan desincronizar.
#
# Es exactamente el defecto que la auditoria encontro en pix-admin: codigo BIFURCADO
# entre lo desplegado (v3.3.0) y lo local (v2.0), con rutas rotas en produccion porque
# nadie sabia cual era la buena.
set -euo pipefail

REPO="${1:-https://github.com/Ncamargo50/pixadvisor-monitor.git}"
RAMA="monitor-deploy"

echo "Publicando PIX_ALERTA -> $REPO"
echo

# La rama se rehace cada vez: es derivada, no se edita a mano.
git branch -D "$RAMA" 2>/dev/null || true
git subtree split --prefix=PIX_ALERTA -b "$RAMA" >/dev/null
echo "  rama $RAMA generada desde PIX_ALERTA/"

# --force porque la rama derivada se recrea entera en cada publicacion. El historial
# real y unico es el del workspace.
git push --force "$REPO" "$RAMA:main"
echo
echo "OK. La corrida programada toma los cambios en su proxima ejecucion."
echo "Para probar ya:  gh workflow run pixadvisor-monitor --repo Ncamargo50/pixadvisor-monitor"
