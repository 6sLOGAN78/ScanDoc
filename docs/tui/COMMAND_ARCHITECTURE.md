# Go TUI Command Architecture Specification

## Command Registry & Palette Engine

The `CommandRegistry` maps keyboard shortcuts and command palette search items to application use cases:

```go
package commands

type CommandSpec struct {
    ID           string
    Title        string
    Category     string
    Keybinding   string
    Description  string
    TargetScreen string
}

type CommandRegistry struct {
    commands map[string]CommandSpec
}
```

## Default Command Specifications

| Command ID | Title | Category | Keybinding | Target Screen |
|---|---|---|---|---|
| `file.open` | Open Document File | File | `Ctrl+O` / `o` | `file_picker` |
| `folder.open` | Open Folder Workspace | File | `Ctrl+F` / `f` | `folder_picker` |
| `pipeline.config` | Configure Pipeline Engine | Pipeline | `p` | `pipeline_config` |
| `models.manager` | Manage Local ML Models | Models | `m` | `model_manager` |
| `benchmark.run` | Run Performance Benchmark | Tools | `b` | `benchmark` |
| `server.manage` | REST Server Manager | Tools | `s` | `server_manager` |
| `export.studio` | Multi-Format Exporter Studio | Export | `e` | `export` |
| `document.inspector` | Inspect DocumentIR Structure | View | `3` | `document_inspector` |
| `command.palette` | Open Command Palette | View | `Ctrl+P` / `>` | `command_palette` |
| `settings.open` | System Settings | System | `8` | `settings` |
| `help.open` | Help & Keyboard Guide | System | `?` / `h` | `help` |

## Command Search & Fuzzy Filtering

The `CommandPalette` screen allows users to type queries to filter commands by `Title`, `Category`, or `Description`.
