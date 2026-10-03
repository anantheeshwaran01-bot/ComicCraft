from typing import List

from pydantic import BaseModel, Field, field_validator


class PanelOutline(BaseModel):
    panel_number: int = Field(ge=1)
    title: str
    scene_description: str
    image_prompt: str


class PromptRequest(BaseModel):
    story_prompt: str = Field(
        min_length=3,
        max_length=2000
    )

    character_name: str = Field(
        min_length=1,
        max_length=80
    )

    setting: str = Field(
        min_length=1,
        max_length=120
    )

    tone: str = Field(
        min_length=1,
        max_length=80
    )

    art_style: str = Field(
        min_length=1,
        max_length=120
    )

    @field_validator("*")
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty."
            )

        return value


class PanelStory(BaseModel):
    panel_number: int
    narration: str
    dialogue: str
    caption: str


class ComicPanel(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str
    image_url: str
    narration: str
    dialogue: str
    caption: str


class ComicResponse(BaseModel):
    title: str
    panels: List[ComicPanel]
    pdf_url: str