from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

JsonObject = dict[str, Any]


class ExtensibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class MetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    canvas: tuple[float, float] | None = None
    output_prefix: str | None = None
    native_lcd_pixels: tuple[int, int] | None = None
    artwork_viewbox: tuple[float, float] | None = None
    model_id: str | None = None
    main_key_count: int | None = None


class PathModel(ExtensibleModel):
    id: str
    d: str | None = None
    source_path: str | None = None

    @model_validator(mode="after")
    def validate_geometry_source(self) -> PathModel:
        if self.d is None and self.source_path is None:
            raise ValueError("path requires either d or source_path")
        return self


class DisplayModel(ExtensibleModel):
    bezel_ref: str | None = None
    bezel: str | None = None
    screen: tuple[float, float, float, float, float] | None = None
    screen_path: str | None = None


class HeaderModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float | None = None
    top_y: float | None = None
    model_x: float | None = None
    second_y: float | None = None
    font_size: float | None = None
    triangle_y: tuple[float, float] | None = None
    triangle_half_width: float | None = None
    brand_text: str | None = None
    brand_font: str | None = None
    brand_model_gap: float | None = None
    model_text: str | None = None
    subtitle: str | None = None
    text_color: str | None = None
    triangle_color: str | None = None
    triangle_char_index: int | None = None
    triangle_x: float | None = None
    triangle_x_offset: float | None = None
    triangle_ink_anchor: bool | None = None
    triangle_after_last_char_positions: float | None = None
    model_tracking: float | None = None
    subtitle_tracking: float | None = None
    show_triangle: bool | None = None


class KeyModel(ExtensibleModel):
    id: str
    width: float
    label: str
    kind: str
    cx: float | None = None


class KeyRowModel(ExtensibleModel):
    id: str
    center_y: float
    default_size: float
    height: float
    keys: list[KeyModel]


class KeyboardModel(ExtensibleModel):
    rows: list[KeyRowModel] | None = None
    key_overrides: dict[str, JsonObject] | None = None


class FunctionKeyItemModel(ExtensibleModel):
    label: str
    letter: str
    top: str | None = None


class FunctionKeysModel(ExtensibleModel):
    items: list[FunctionKeyItemModel] | None = None


class RawDesignModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extends: list[str] = Field(default_factory=list)
    metadata: MetadataModel | None = None
    fonts: dict[str, str] | None = None
    palette: dict[str, str] | None = None
    gradients: dict[str, list[str]] | None = None
    paths: list[PathModel] | None = None
    path_remove: list[str] | None = None
    path_overrides: dict[str, JsonObject] | None = None
    display: DisplayModel | None = None
    logo: JsonObject | None = None
    header: HeaderModel | None = None
    function_keys: FunctionKeysModel | None = None
    nav: JsonObject | None = None
    keyboard: KeyboardModel | None = None
    modifiers: JsonObject | None = None


class ResolvedDesignModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: MetadataModel
    fonts: dict[str, str]
    palette: dict[str, str]
    gradients: dict[str, list[str]]
    paths: list[PathModel]
    display: DisplayModel
    logo: JsonObject
    header: HeaderModel
    function_keys: FunctionKeysModel
    nav: JsonObject
    keyboard: KeyboardModel
    modifiers: JsonObject

    @model_validator(mode="after")
    def validate_build_identity(self) -> ResolvedDesignModel:
        if self.metadata.name is None:
            raise ValueError("resolved design metadata.name is required")
        if self.metadata.canvas is None:
            raise ValueError("resolved design metadata.canvas is required")
        if self.metadata.output_prefix is None:
            raise ValueError("resolved design metadata.output_prefix is required")
        if self.keyboard.rows is None:
            raise ValueError("resolved design keyboard.rows is required")
        expected_lcd = {
            "hp39gplus": (131, 64),
            "hp39gs": (131, 64),
            "hp40gs": (131, 64),
            "hp48gii": (131, 64),
            "hp49gplus": (131, 80),
            "hp50g": (131, 80),
        }
        model_id = self.metadata.model_id
        if model_id in expected_lcd and self.metadata.native_lcd_pixels != expected_lcd[model_id]:
            raise ValueError(
                f"{model_id} native_lcd_pixels must be {expected_lcd[model_id]}, "
                f"got {self.metadata.native_lcd_pixels}"
            )
        return self


def validate_raw_design(data: JsonObject) -> None:
    RawDesignModel.model_validate(data)


def validate_resolved_design(data: JsonObject) -> None:
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata.get("output_prefix") is not None:
        ResolvedDesignModel.model_validate(data)
