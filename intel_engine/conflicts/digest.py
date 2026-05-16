"""Render a ConflictDigest as Slack Block Kit blocks."""
from intel_engine.schemas.conflict import ConflictDigest


def to_slack_blocks(digest: ConflictDigest) -> list[dict]:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"KB Conflicts — week ending {digest.week_end}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{digest.count}* conflict(s) detected.",
            },
        },
    ]
    for i, c in enumerate(digest.conflicts, start=1):
        entries_block = "\n".join(f"• `{e}`" for e in c.entries)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{i}. [{c.domain}] {c.fact_topic}*\n"
                        f"{entries_block}\n"
                        f"_Proposed canonical:_ `{c.canonical_proposal}`\n"
                        f"_Reason:_ {c.reasoning}"
                    ),
                },
            }
        )
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Accept proposal"},
                        "value": f"accept:{c.canonical_proposal}",
                        "action_id": f"conflict_accept_{i}",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "value": f"reject:{c.fact_topic}",
                        "action_id": f"conflict_reject_{i}",
                    },
                ],
            }
        )
    return blocks
