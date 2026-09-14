"""The "what's new" changelog shown to a user once per unseen release.

English only, deliberately -- see DESIGN.md's "What's new dialog" section for
why this content carries no i18n keys. WHATS_NEW is the single source of
truth for both the dialog's content and the current version it gates on;
nothing here is derived from pyproject.toml or importlib.metadata.

Baseline is 0.1.18 (no entry, nothing to show); entries accumulate from
0.1.19 onwards, newest first.
"""

WHATS_NEW = [
    {
        "version": "0.1.19",
        "changes": [
            "Edit your own name, email and phone from a new profile page.",
            "Loan views show who handed equipment out and who accepted it "
            "back -- click their name for contact details.",
            "The new-loan form now keeps your draft if you navigate away "
            "mid-entry.",
            "This what's new dialog.",
        ],
    },
]

CURRENT_VERSION = WHATS_NEW[0]["version"]


def is_unseen(seen_version, entries=WHATS_NEW, current_version=None):
    """Whether `seen_version` means the current release is still unseen.

    Compares by *index position* in `entries` (ordered newest first), never
    lexically: "0.1.9" sorts above "0.1.18" as a string, which would make a
    naive string compare stop firing the dialog once double-digit patch
    versions show up. A `seen_version` that isn't in the list at all --
    blank, or older than the tracked baseline -- means "show everything".
    """
    if current_version is None:
        current_version = entries[0]["version"]
    versions = [entry["version"] for entry in entries]
    if not seen_version or seen_version not in versions:
        return True
    return versions.index(seen_version) > versions.index(current_version)
