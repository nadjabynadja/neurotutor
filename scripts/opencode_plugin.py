#!/usr/bin/env python3
"""
NeuroTutor OpenCode Plugin

Allows natural language control of OpenCode for NeuroTutor development.
Usage: python opencode_plugin.py "<natural language command>"
"""
import subprocess
import sys
import os
import json
import re
from pathlib import Path

# Configuration
OPENCODE_PATH = "/root/.opencode/bin/opencode"
PROJECT_PATH = "/root/.openclaw/workspace/NeuroTutor"
MODEL = "minimax"  # or specify model


class OpenCodePlugin:
    def __init__(self, project_path: str = PROJECT_PATH):
        self.project_path = Path(project_path)
        self.opencode_bin = OPENCODE_PATH
    
    def execute(self, command: str, timeout: int = 120) -> dict:
        """
        Execute an OpenCode command in natural language.
        
        Args:
            command: Natural language command
            timeout: Timeout in seconds
            
        Returns:
            dict with keys: success, output, error
        """
        # Build the full command
        # OpenCode expects: opencode [-m model] [project] "message"
        cmd = [
            self.opencode_bin,
            "-m", MODEL,
            str(self.project_path),
            command
        ]
        
        # Set up environment
        env = os.environ.copy()
        env["PATH"] = f"/root/.opencode/bin:" + env.get("PATH", "")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_path),
                env=env
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": -1
            }
    
    def parse_nl_command(self, nl_command: str) -> str:
        """
        Convert natural language to OpenCode-appropriate command.
        
        This is a simple heuristic - OpenCode is already good at
        understanding natural language, so we mostly pass through.
        """
        # Clean up the command
        command = nl_command.strip()
        
        # If it doesn't start with a verb, might need tweaking
        # But OpenCode is designed to understand NL, so pass through
        return command


def format_output(result: dict) -> str:
    """Format the result for display."""
    output = []
    
    if result["success"]:
        output.append("✅ OpenCode executed successfully:\n")
    else:
        output.append("❌ OpenCode encountered an issue:\n")
    
    if result.get("output"):
        output.append(result["output"])
    
    if result.get("error"):
        output.append(f"\nErrors:\n{result['error']}")
    
    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python opencode_plugin.py <natural language command>")
        print("\nExamples:")
        print('  python opencode_plugin.py "Add a new API endpoint for getting student progress"')
        print('  python opencode_plugin.py "Fix the bug in attention detection"')
        print('  python opencode_plugin.py "Write tests for the directive engine"')
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    print(f"🎯 Executing: {command}\n")
    
    plugin = OpenCodePlugin()
    result = plugin.execute(command)
    print(format_output(result))
