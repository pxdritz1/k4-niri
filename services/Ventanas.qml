pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io as Io

Singleton {
    id: ventanas

    property var recientes: []
    property string pidActivo: ""

    readonly property var lista: {
        const abiertas = Niri.windows.slice()
        const salida = []
        for (let i = 0; i < recientes.length; ++i) {
            const id = recientes[i]
            const index = abiertas.findIndex(window => String(window.id) === id)
            if (index >= 0)
                salida.push(abiertas.splice(index, 1)[0])
        }
        return salida.concat(abiertas)
    }

    readonly property int count: lista.length

    readonly property var espaciosVistos: {
        const ids = ({})
        const workspaces = Niri.workspaces
        for (let i = 0; i < workspaces.length; ++i) {
            const workspace = workspaces[i]
            if (workspace.is_active)
                ids[workspace.id] = true
        }
        return ids
    }

    function seVe(window) {
        return !!(window && espaciosVistos[window.workspace_id] === true)
    }

    function refrescar() {}

    function datos(window) { return window || ({}) }
    function direccion(window) { return window ? String(window.id) : "" }
    function clase(window) { return String(datos(window).app_id || "") }
    function tituloVentana(window) { return String(datos(window).title || "") }
    function espacio(window) {
        const id = datos(window).workspace_id
        return id === undefined || id === null ? "" : String(id)
    }

    function icono(window) {
        const id = clase(window)
        if (!id)
            return ""
        let path = Quickshell.iconPath(id, true)
        if (path) return path
        path = Quickshell.iconPath(id.toLowerCase(), true)
        if (path) return path
        const apps = DesktopEntries.applications.values
        const low = id.toLowerCase()
        for (let i = 0; i < apps.length; ++i) {
            const app = apps[i]
            const appId = String(app.id || "").toLowerCase()
            if (appId === low || appId.indexOf(low) !== -1
                || String(app.name || "").toLowerCase() === low) {
                const found = Quickshell.iconPath(app.icon, true)
                if (found) return found
            }
        }
        return ""
    }

    function titulo(window) {
        const id = clase(window).toLowerCase()
        if (!id)
            return Idioma.t("Ventana")
        const apps = DesktopEntries.applications.values
        for (let i = 0; i < apps.length; ++i) {
            if (String(apps[i].id || "").toLowerCase() === id)
                return apps[i].name || clase(window)
        }
        return clase(window)
    }

    function activar(window) {
        const id = direccion(window)
        if (id)
            ejecutar(["niri", "msg", "action", "focus-window", "--id", id])
    }

    function cerrar(window) {
        const id = direccion(window)
        if (id)
            ejecutar(["niri", "msg", "action", "close-window", "--id", id])
    }

    function ejecutar(command) {
        if (action.running)
            return
        actionCommand = command
        action.running = true
    }

    property var actionCommand: []
    Io.Process {
        id: action
        command: ventanas.actionCommand
        running: false
        onExited: running = false
    }

    onWindowsChanged: {
        const focused = Niri.windows.find(window => window.is_focused)
        pidActivo = focused && focused.pid !== undefined ? String(focused.pid) : ""
        if (!focused)
            return
        const id = String(focused.id)
        recientes = [id].concat(recientes.filter(item => item !== id)).slice(0, 40)
    }
}
