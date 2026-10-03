from typing import List


def build_comic_layout(
    outline: List[dict],
    stories: List[dict],
    image_urls: List[str],
) -> List[dict]:

    story_by_panel = {
        item["panel_number"]: item
        for item in stories
    }

    layout = []

    for index, panel in enumerate(outline):

        story = story_by_panel.get(
            panel["panel_number"],
            {}
        )

        layout.append(
            {
                **panel,

                "image_url":
                    image_urls[index],

                "narration":
                    story.get(
                        "narration",
                        ""
                    ),

                "dialogue":
                    story.get(
                        "dialogue",
                        ""
                    ),

                "caption":
                    story.get(
                        "caption",
                        ""
                    ),
            }
        )

    return layout