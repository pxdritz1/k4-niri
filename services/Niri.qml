pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io as Io

Singleton {
    id: root
    property var workspaces: []
    property var windows: []
    property var outputs: []
    property string focusedOutput: ""
    property bool connected: false
    property string lastError: ""
    property var pendingActions: []
    property bool actionRunning: false

    function handleLine(line) {
        let event
        try { event = JSON.parse(line) }
        catch (error) { console.warn("K4 Niri IPC: invalid event JSON", error); return }
        const name = Object.keys(event)[0]
        const data = event[name]
        if (!name || data === undefined) return

        switch (name) {
        case "WorkspacesChanged":
            workspaces = data.workspaces || []
            updateFocusedOutput()
            break
        case "WorkspaceActivated": {
            const activated = workspaces.find(item => item.id === data.id)
            const output = activated ? activated.output : null
            workspaces = workspaces.map(item => Object.assign({}, item, {
                is_active: item.id === data.id ? true
                    : (output && item.output === output ? false : item.is_active),
                is_focused: data.focused
                    ? item.id === data.id
                    : (item.id === data.id ? false : item.is_focused)
            }))
            updateFocusedOutput()
            break
        }
        case "WindowsChanged":
            windows = data.windows || []
            break
        case "WindowOpenedOrChanged": {
            if (!data.window) break
            const next = windows.slice()
            const index = next.findIndex(item => item.id === data.window.id)
            if (index < 0) next.push(data.window)
            else next[index] = data.window
            windows = next
            break
        }
        case "WindowClosed":
            windows = windows.filter(item => item.id !== data.id)
            break
        case "WindowFocusChanged":
            windows = windows.map(item => Object.assign({}, item, { is_focused: item.id === data.id }))
            break
        case "OutputsChanged":
            outputs = data.outputs || []
            break
        case "ConfigLoaded":
            lastError = ""
            break
        }
    }

    function updateFocusedOutput() {
        const focused = workspaces.find(item => item.is_focused)
        focusedOutput = focused && focused.output ? String(focused.output) : ""
    }

    function action(name, args) {
        if (!name || !/^[a-z][a-z0-9-]*$/.test(name)) return false
        const command = ["niri", "msg", "action", name]
        for (let i = 0; i < (args || []).length; ++i) command.push(String(args[i]))
        pendingActions = pendingActions.concat([command])
        runNextAction()
        return true
    }

    function focusWindow(id) { return action("focus-window", ["--id", id]) }
    function closeWindow(id) { return action("close-window", ["--id", id]) }
    function toggleFullscreen(id) {
        return action("fullscreen-window", id === undefined ? [] : ["--id", id])
    }
    function toggleFloating(id) {
        return action("toggle-window-floating", id === undefined ? [] : ["--id", id])
    }
    function focusWorkspace(index) { return action("focus-workspace", [index]) }
    function focusWorkspaceDown() { return action("focus-workspace-down") }
    function focusWorkspaceUp() { return action("focus-workspace-up") }
    function toggleOverview() { return action("toggle-overview") }
    function reloadConfig() { return action("load-config-file") }
    function quit() { return action("quit", ["--skip-confirmation"]) }

    function runNextAction() {
        if (actionRunning || pendingActions.length === 0) return
        const next = pendingActions[0]
        pendingActions = pendingActions.slice(1)
        actionProcess.command = next
        actionRunning = true
        actionProcess.running = true
    }

    Io.SplitParser { id: eventParser; onRead: line => root.handleLine(line) }

    Io.Process {
        id: eventStream
        command: ["niri", "msg", "--json", "event-stream"]
        running: true
        stdout: eventParser
        stderr: Io.SplitParser {
            onRead: line => {
                if (String(line).trim().length > 0) root.lastError = String(line)
            }
        }
        onStarted: root.connected = true
        onExited: { root.connected = false; reconnect.restart() }
    }

    Io.Process {
        id: actionProcess
        onExited: function (code) {
            root.actionRunning = false
            if (code !== 0)
                root.lastError = "niri action failed: " + actionProcess.command.join(" ")
            root.runNextAction()
        }
    }

    Timer {
        id: reconnect
        interval: 1500
        repeat: false
        onTriggered: eventStream.running = true
    }
}
