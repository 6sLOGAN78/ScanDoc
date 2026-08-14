"""
Command Registry mapping keyboard shortcuts and command palette items to Application Layer use cases.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class CommandSpec:
    command_id: str
    title: str
    category: str
    keybinding: Optional[str] = None
    description: str = ""
    target_screen: Optional[str] = None


class CommandRegistry:
    """
    Centralized Command Registry decoupling input bindings and command palette search
    from UI rendering and business logic.
    """

    def __init__(self):
        self._commands: Dict[str, CommandSpec] = {}

        # Default Registered Commands
        self.register(CommandSpec("file.open", "Open Document File", "File", "Ctrl+O / o", "Open interactive file browser", "file_picker"))
        self.register(CommandSpec("folder.open", "Open Folder Workspace", "File", "Ctrl+F / f", "Open interactive folder browser", "folder_picker"))
        self.register(CommandSpec("pipeline.config", "Configure Pipeline Engine", "Pipeline", "p", "Open pipeline stage editor", "pipeline_config"))
        self.register(CommandSpec("models.manager", "Manage Local ML Models", "Models", "m", "Open model lifecycle dashboard", "model_manager"))
        self.register(CommandSpec("benchmark.run", "Run Performance Benchmark", "Tools", "b", "Run benchmark suite vs Docling", "benchmark"))
        self.register(CommandSpec("server.manage", "REST Server Manager", "Tools", "s", "Start/stop REST API & Web Studio", "server_manager"))
        self.register(CommandSpec("export.studio", "Multi-Format Exporter Studio", "Export", "e", "Export DocumentIR to target format", "export"))
        self.register(CommandSpec("document.inspector", "Inspect DocumentIR Structure", "View", "3", "Inspect block tree and page IR", "document_inspector"))
        self.register(CommandSpec("command.palette", "Open Command Palette", "View", "Ctrl+P / >", "Quick action search modal", "command_palette"))
        self.register(CommandSpec("settings.open", "System Settings", "System", "8", "Configure offline mode and devices", "settings"))
        self.register(CommandSpec("help.open", "Help & Keyboard Guide", "System", "? / h", "Keyboard shortcut reference", "help"))

    def register(self, spec: CommandSpec) -> None:
        self._commands[spec.command_id] = spec

    def list_commands(self, filter_query: Optional[str] = None) -> List[CommandSpec]:
        cmds = list(self._commands.values())
        if filter_query:
            q = filter_query.lower()
            cmds = [c for c in cmds if q in c.title.lower() or q in c.category.lower() or q in c.description.lower()]
        return cmds

    def lookup_keybinding(self, keybinding: str) -> Optional[CommandSpec]:
        for cmd in self._commands.values():
            if cmd.keybinding and keybinding.lower() in cmd.keybinding.lower():
                return cmd
        return None


default_command_registry = CommandRegistry()
