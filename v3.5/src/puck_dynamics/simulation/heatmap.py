from __future__ import annotations
import numpy as np
from pathlib import Path

class Heatmap:
    def __init__(self, shape: tuple[int,int]):
        self.arr = np.zeros(shape, dtype=np.uint32)

    def increment(self, idx: tuple[int,int]) -> None:
        self.arr[idx] += 1

    def normalised(self) -> np.ndarray:
        total = self.arr.sum()
        return self.arr.astype(np.float64) / total if total else self.arr

    def save_npy(self, path: str | Path) -> None:
        np.save(path, self.arr)
