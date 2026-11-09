pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io as Io

Singleton {
    id: root

    property var workspaces: []
    property var windows: []
    property var fullscreenByOutput: ({})
    property string focusedOutput: ""
    property bool connected: false

    function handleLine(line) {
        let event
        try {
            event = JSON.parse(line)
        } catch (error) {
            console.warn("K4 Niri IPC: invalid event JSON", error)
            return
        }

        const name = Object.keys(event)[0]
        const data = event[name]
        if (!name || !data)
            return

        if (name === "WorkspacesChanged") {
            workspaces = data.workspaces || []
            updateFocusedOutput()
            updateFullscreen()
        } else if (name === "WorkspaceActivated") {
            const next = workspaces.slice()
            for (let i = 0; i < next.length; ++i) {
                if (next[i].id === data.id)
                    next[i] = Object.assign({}, next[i], { is_active: true, is_focused: !!data.focused })
                else if (data.focused)
                    next[i] = Object.assign({}, next[i], { is_focused: false })
            }
            workspaces = next
            updateFocusedOutput()
        } else if (name === "WindowsChanged") {
            windows = data.windows || []
            updateFullscreen()
        } else if (name === "WindowOpenedOrChanged") {
            const next = windows.slice()
            const window = data.window
            const index = next.findIndex(item => item.id === window.id)
            if (index < 0)
                next.push(window)
            else
                next[index] = window
            windows = next
            updateFullscreen()
        } else if (name === "WindowClosed") {
            windows = windows.filter(item => item.id !== data.id)
            updateFullscreen()
        } else if (name === "WindowFocusChanged") {
            const next = windows.map(item => Object.assign({}, item, { is_focused: item.id === data.id }))
            windows = next
            updateFocusedOutput()
        }
    }

    function updateFocusedOutput() {
        const focused = workspaces.find(item => item.is_focused)
        if (focused && focused.output)
            focusedOutput = String(focused.output)
    }

    function updateFullscreen() {
        const result = ({})
        for (let i = 0; i < workspaces.length; ++i) {
            const workspace = workspaces[i]
            const output = String(workspace.output || "")
            if (!output)
                continue
            const hasFullscreen = windows.some(window =>
                window.workspace_id === workspace.id && !!window.is_fullscreen)
            result[output] = hasFullscreen
        }
        fullscreenByOutput = result
    }

    Io.SplitParser {
        id: eventParser
        onRead: line => root.handleLine(line)
    }

    Io.Process {
        id: eventStream
        command: ["niri", "msg", "--json", "event-stream"]
        running: true
        stdout: eventParser
        onStarted: root.connected = true
        onExited: root.connected = false
    }
}
