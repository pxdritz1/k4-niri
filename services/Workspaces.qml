pragma Singleton

import QtQuick
import Quickshell

Singleton {
    readonly property var list: {
        const values = Niri.workspaces.slice()
        values.sort(function (a, b) {
            const ai = a.idx === undefined ? a.id : a.idx
            const bi = b.idx === undefined ? b.id : b.idx
            return ai - bi
        })
        return values
    }

    readonly property int activo: {
        for (let i = 0; i < list.length; ++i)
            if (list[i].is_focused)
                return list[i].id
        return -1
    }

    readonly property int dotsWidth: list.length === 0
        ? 0 : (list.length - 1) * 10 + 18 + 8

    readonly property var llenos: Niri.fullscreenByOutput

    function lleno(pantalla) {
        return llenos[String(pantalla)] === true
    }
}
