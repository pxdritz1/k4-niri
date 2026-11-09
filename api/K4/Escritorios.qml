pragma Singleton
import QtQuick

QtObject {
    readonly property var lista: Workspaces.list
    readonly property int activo: Workspaces.activo
    function lleno(pantalla) { return Workspaces.lleno(pantalla) }
    function focar(referencia) {
        const valor = String(referencia)
        const porId = Workspaces.list.find(item => String(item.id) === valor)
        const workspace = porId || Workspaces.list.find(item =>
            String(item.idx) === valor || item.name === valor)
        if (!workspace)
            return false
        return Niri.focusWorkspace(workspace.name || workspace.idx)
    }
}
