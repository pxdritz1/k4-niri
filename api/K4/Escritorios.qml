pragma Singleton
import QtQuick

QtObject {
    readonly property var lista: Workspaces.list
    readonly property int activo: Workspaces.activo
    function lleno(pantalla) { return Workspaces.lleno(pantalla) }
    function focar(indice) { return Niri.focusWorkspace(indice) }
}
