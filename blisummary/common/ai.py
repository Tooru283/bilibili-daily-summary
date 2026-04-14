import subprocess

from blisummary.config import CLAUDE_CLI



def run_claude_prompt(prompt: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLAUDE_CLI, "-p", prompt],
        capture_output=True,
        text=True,
    )
