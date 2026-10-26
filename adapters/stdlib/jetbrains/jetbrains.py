"""jetbrains.py: willow in IntelliJ, PyCharm and the other JetBrains IDEs. Python 3.9+.

    python adapters/stdlib/jetbrains/jetbrains.py --box DIR

Prints an external tool, willow, that asks for a question and prints each answer as a link to its file and line. The lines go in External Tools.xml in the IDE's config folder, under tools/ (or Settings, Tools, External Tools, with the same values); it changes nothing itself.
Each answer comes from pipe (adapters/stdlib/pipe/pipe.py --grep), so every
question is the kernel's own bite, on the record.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hosts"))
import hosts  # noqa: E402

PIPE = hosts.PIPE


def snippet(box: Path, py: str) -> str:
    # the IDE splits PARAMETERS where Windows would: double quotes hold a piece
    params = subprocess.list2cmdline([str(PIPE), "--box", str(box.resolve()), "--grep"])
    params += ' "$Prompt$"'
    return (
        '<toolSet name="External Tools">\n'
        '  <tool name="willow" description="Ask your willow folder" showInMainMenu="true" '
        'showInEditor="true" showInProject="true" showInSearchPopup="true" disabled="false" '
        'useConsole="true" showConsoleOnStdOut="false" showConsoleOnStdErr="false" '
        'synchronizeAfterRun="false">\n'
        "    <exec>\n"
        f'      <option name="COMMAND" value={quoteattr(py)} />\n'
        f'      <option name="PARAMETERS" value={quoteattr(params)} />\n'
        '      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$" />\n'
        "    </exec>\n"
        "    <filter>\n"
        '      <option name="NAME" value="willow" />\n'
        '      <option name="DESCRIPTION" value="file and line" />\n'
        '      <option name="REGEXP" value="$FILE_PATH$:$LINE$:" />\n'
        "    </filter>\n"
        "  </tool>\n"
        "</toolSet>\n"
    )


def render(box: Path, py: str = None) -> str:
    return (
        "Add this to External Tools.xml in the IDE's config folder, under tools/ (or Settings, Tools, External Tools, with the same values):\n\n"
        + snippet(box, py or sys.executable or "python3")
    )


def main(argv: list[str]) -> int:
    return hosts.cli(__doc__, render, argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
