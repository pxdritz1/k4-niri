// Niri does not expose an application-side GlobalShortcut protocol.
// Declare the key in ~/.config/niri/config.kdl and call a K4 IPC target.
import QtQuick
Item {
    property string name: ""
    readonly property bool disponible: false
    signal activated()
}
