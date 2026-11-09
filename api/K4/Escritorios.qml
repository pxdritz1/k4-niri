pragma Singleton
import QtQuick

QtObject {
    readonly property var lista: Workspaces.list
    readonly property int activo: Workspaces.activo
    function lleno(pantalla) { return Workspaces.lleno(pantalla) }
    function focar(referencia) {
        const porId = Workspaces.list.find(item => item.id === referencia)
        const workspace = porId || Workspaces.list.find(item =>
            item.idx === referencia || item.name === String(referencia))
        if (!workspace)
            return false
        return Niri.focusWorkspace(workspace.name || workspace.idx)
    }
}
