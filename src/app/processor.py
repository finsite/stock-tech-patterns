"""
Module to process stock data for classic chart pattern detection.

Includes detection of:
- Double Top / Bottom
- Head and Shoulders (basic form)
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from app.logger import setup_logger
from app.output_handler import send_to_output

logger = setup_logger(__name__)


def analyze_patterns(data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyzes stock price data to detect classic chart patterns.

    Args:
    ----
        data (dict[str, Any]): Incoming stock data payload with 'data' key.

    Returns:
    -------
        dict[str, Any]: Analysis result.

    Args:
      data: dict[str:
      Any]:

    Returns:
    """
    try:
        symbol = data.get("symbol", "UNKNOWN")
        price_data = data.get("data")

        if not price_data:
            raise ValueError("Missing 'data' field.")

        df = pd.DataFrame(price_data)
        if df.empty or "close" not in df.columns:
            raise ValueError("Data must contain non-empty 'close' prices.")

        close_prices = df["close"].astype(float).to_numpy()
        patterns = []

        # Detect peaks and valleys
        peaks, _ = find_peaks(close_prices)
        valleys, _ = find_peaks(-close_prices)

        logger.info("Found %d peaks and %d valleys for %s", len(peaks), len(valleys), symbol)

        # Double Top Detection
        if len(peaks) >= 2:
            peak_values = close_prices[peaks]
            peak_diff = np.abs(peak_values[-1] - peak_values[-2])
            if peak_diff / peak_values[-2] < 0.02:
                patterns.append("Double Top")

        # Double Bottom Detection
        if len(valleys) >= 2:
            valley_values = close_prices[valleys]
            valley_diff = np.abs(valley_values[-1] - valley_values[-2])
            if valley_diff / valley_values[-2] < 0.02:
                patterns.append("Double Bottom")

        # Head and Shoulders (basic detection: peak-valley-peak-valley-peak)
        if len(peaks) >= 3 and len(valleys) >= 2:
            last3_peaks = close_prices[peaks[-3:]]
            last2_valleys = close_prices[valleys[-2:]]

            if (
                last3_peaks[1] > last3_peaks[0]
                and last3_peaks[1] > last3_peaks[2]
                and last2_valleys[0] < last3_peaks[1]
                and last2_valleys[1] < last3_peaks[1]
            ):
                patterns.append("Head and Shoulders")

        result = {
            "symbol": symbol,
            "analysis_type": "chart_patterns",
            "analysis_data": {
                "patterns": patterns or ["No recognizable patterns"],
                "peaks": peaks.tolist(),
                "valleys": valleys.tolist(),
            },
        }

        send_to_output(result)
        return result

    except Exception as e:
        logger.exception("Pattern analysis failed for symbol %s", data.get("symbol", "UNKNOWN"))
        return {
            "symbol": data.get("symbol", "UNKNOWN"),
            "analysis_type": "chart_patterns",
            "error": str(e),
        }
