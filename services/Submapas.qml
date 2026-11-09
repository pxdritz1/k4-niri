pragma Singleton

import QtQuick

Singleton {
    // Niri does not provide Hyprland-style keyboard submaps.
    readonly property string actual: ""
    readonly property bool disponible: false
}
