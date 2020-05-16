from typing import Dict
from uuid import uuid4

from gilgamesh.log import Log


def apply_renames(log: Log, renamed_labels: Dict[str, str]) -> None:
    def apply(labels: Dict[str, str], dry=False) -> None:
        """Naively perform label renames."""
        for old, new in labels.items():
            log.rename_label(old, new, dry=dry)

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


def unique_label(orig_label: str) -> str:
    """Return a unique label. Respects locality (i.e. if orig_label
    starts with a dot, the generated label will also start with a dot."""
    return orig_label[0] + "l" + uuid4().hex
    # TODO: check for meteors.
