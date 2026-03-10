from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

__all__ = ["MatplotlibThemeService"]

logger = logging.getLogger(__name__)

matplotlib.use("Agg")


class MatplotlibThemeService:
    _initialized = False

    @classmethod
    def init(cls) -> None:
        if cls._initialized:
            return

        plt.rcParams.update({
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.figsize": (8, 6),
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.1,
        })

        # Try to register CJK font
        font_path = Path(__file__).parent.parent.parent / "assets" / "fonts" / "NotoSansSC-Regular.otf"
        if font_path.exists():
            try:
                from matplotlib import font_manager
                font_manager.fontManager.addfont(str(font_path))
                plt.rcParams["font.family"] = "Noto Sans SC"
                logger.info("CJK font loaded: %s", font_path)
            except Exception as e:
                logger.warning("Failed to load CJK font: %s", e)
        else:
            logger.info("CJK font not found at %s, using defaults", font_path)

        cls._initialized = True
