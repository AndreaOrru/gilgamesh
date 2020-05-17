from typing import Dict, Optional
from uuid import uuid4

from gilgamesh.log import Log
from gilgamesh.subroutine import Subroutine


def apply_renames(
    log: Log, renamed_labels: Dict[str, str], subroutine: Optional[Subroutine] = None
) -> None:
    def apply(labels: Dict[str, str], dry=False) -> None:
        """Naively perform label renames."""
        for old, new in labels.items():
            log.rename_label(old, new, subroutine, dry=dry)

    # Rename labels to temporary unique labels.
    temp_renamed_labels = {old: unique_label(old) for old in renamed_labels.keys()}
    # Perform a dry run to make sure there are no errors
    # when renames are applied to the full disassembly.
    apply(temp_renamed_labels, dry=True)
    # Actually apply the renames if everything was ok.
    apply(temp_renamed_labels)

    # Re-rename the unique labels to the target labels.
    renamed_labels = {
        unique_label: renamed_labels[old]
        for old, unique_label in temp_renamed_labels.items()
    }
    apply(renamed_labels)
    # NOTE: this is needed when swapping pairs of labels.


def apply_local_renames(
    subroutine: Subroutine, renamed_labels: Dict[str, str]
) -> Dict[str, str]:
    """Safely perform bulk label renames."""

    # Separate local and global renames.
    local_renames = {}
    global_renames = {}
    for old, new in renamed_labels.items():
        if old[0] == ".":
            local_renames[old] = new
        else:
            global_renames[old] = new

    # We only apply the local renames here.
    apply_renames(subroutine.log, local_renames, subroutine)
    # We return the global ones for a later stage.
    return global_renames


def unique_label(orig_label: str) -> str:
    """Return a unique label. Respects locality (i.e. if orig_label
    starts with a dot, the generated label will also start with a dot."""
    return orig_label[0] + "l" + uuid4().hex
    # TODO: check for meteors.
