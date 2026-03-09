from enum import StrEnum


class Color(StrEnum):
    # Reds
    RED = "red"
    CRIMSON = "crimson"
    CORAL = "coral"
    SALMON = "salmon"

    # Oranges
    ORANGE = "orange"
    AMBER = "amber"
    PEACH = "peach"

    # Yellows
    YELLOW = "yellow"
    GOLD = "gold"
    LEMON = "lemon"

    # Greens
    GREEN = "green"
    LIME = "lime"
    MINT = "mint"
    FOREST = "forest"
    OLIVE = "olive"

    # Blues
    BLUE = "blue"
    SKY = "sky"
    NAVY = "navy"
    OCEAN = "ocean"
    ICE = "ice"

    # Cyans / Teals
    CYAN = "cyan"
    TEAL = "teal"
    TURQUOISE = "turquoise"

    # Purples / Violets
    PURPLE = "purple"
    VIOLET = "violet"
    LAVENDER = "lavender"
    INDIGO = "indigo"

    # Pinks / Magentas
    PINK = "pink"
    HOT_PINK = "hot_pink"
    MAGENTA = "magenta"
    ROSE = "rose"

    # Whites (color temperature via RGB approximation)
    WARM_WHITE = "warm_white"
    NEUTRAL_WHITE = "neutral_white"
    COOL_WHITE = "cool_white"
    DAYLIGHT = "daylight"

    # Atmospheric
    SUNSET = "sunset"
    SUNRISE = "sunrise"
    CANDLELIGHT = "candlelight"
    MOONLIGHT = "moonlight"
    NORTHERN_LIGHTS = "northern_lights"


_COLOR_MAP: dict[Color, tuple[int, int, int]] = {
    Color.RED: (255, 0, 0),
    Color.CRIMSON: (220, 20, 60),
    Color.CORAL: (255, 80, 60),
    Color.SALMON: (255, 140, 110),
    Color.ORANGE: (255, 165, 0),
    Color.AMBER: (255, 191, 0),
    Color.PEACH: (255, 200, 150),
    Color.YELLOW: (255, 255, 0),
    Color.GOLD: (255, 215, 0),
    Color.LEMON: (230, 255, 80),
    Color.GREEN: (0, 255, 0),
    Color.LIME: (160, 255, 0),
    Color.MINT: (100, 255, 180),
    Color.FOREST: (30, 120, 50),
    Color.OLIVE: (128, 128, 0),
    Color.BLUE: (0, 0, 255),
    Color.SKY: (100, 180, 255),
    Color.NAVY: (0, 0, 128),
    Color.OCEAN: (0, 80, 200),
    Color.ICE: (180, 230, 255),
    Color.CYAN: (0, 255, 255),
    Color.TEAL: (0, 180, 180),
    Color.TURQUOISE: (50, 210, 190),
    Color.PURPLE: (128, 0, 128),
    Color.VIOLET: (138, 43, 226),
    Color.LAVENDER: (180, 130, 255),
    Color.INDIGO: (75, 0, 130),
    Color.PINK: (255, 105, 180),
    Color.HOT_PINK: (255, 20, 147),
    Color.MAGENTA: (255, 0, 255),
    Color.ROSE: (255, 80, 120),
    Color.WARM_WHITE: (255, 197, 143),
    Color.NEUTRAL_WHITE: (255, 235, 210),
    Color.COOL_WHITE: (220, 235, 255),
    Color.DAYLIGHT: (240, 245, 255),
    Color.SUNSET: (255, 100, 40),
    Color.SUNRISE: (255, 160, 80),
    Color.CANDLELIGHT: (255, 160, 60),
    Color.MOONLIGHT: (180, 190, 230),
    Color.NORTHERN_LIGHTS: (50, 230, 180),
}


def resolve_color(color: Color) -> tuple[int, int, int]:
    return _COLOR_MAP[color]
