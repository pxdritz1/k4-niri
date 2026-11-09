// Niri does not currently expose a Quickshell WaylandToplevel object for
// per-window screencopy. Keep the component API loadable and report the
// capability honestly; callers can fall back to app icons and titles.

import QtQuick
import Quickshell.Wayland

ScreencopyView {
    id: self
    property string direccion: ""
    readonly property bool disponible: false
    captureSource: null
    live: false
}
