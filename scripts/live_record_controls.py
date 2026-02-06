from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np

class ButtonEdgeDetector:
    def __init__(self):
        self._prev_pressed: Dict[tuple[str, str], bool] = {}

    def rising_edge(self, controller_data: dict | None, side: str, key: str) -> bool:
        curr_pressed = bool((controller_data or {}).get(side, {}).get(key, False))
        key_id = (side, key)
        prev_pressed = self._prev_pressed.get(key_id, False)
        self._prev_pressed[key_id] = curr_pressed
        return curr_pressed and not prev_pressed


def make_episode_stem(robot: str, episode_index: int, now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{robot}_{now.strftime('%Y%m%d_%H%M%S')}_ep{episode_index:03d}"


def build_episode_paths(session_dir: str | Path, stem: str) -> tuple[Path, Path]:
    output_dir = Path(session_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{stem}.pkl", output_dir / f"{stem}.json"


@dataclass
class LiveEpisodeBuffer:
    is_recording: bool = False
    qpos_frames: List[np.ndarray] = field(default_factory=list)
    timestamps_ns: List[int] = field(default_factory=list)

    def start(self) -> None:
        self.qpos_frames.clear()
        self.timestamps_ns.clear()
        self.is_recording = True

    def stop(self) -> None:
        self.is_recording = False

    def discard(self) -> None:
        self.is_recording = False
        self.qpos_frames.clear()
        self.timestamps_ns.clear()

    def append(self, qpos: np.ndarray, timestamp_ns: int | None = None) -> None:
        if not self.is_recording:
            return
        self.qpos_frames.append(np.asarray(qpos, dtype=float).copy())
        if timestamp_ns is not None:
            self.timestamps_ns.append(int(timestamp_ns))

    @property
    def frame_count(self) -> int:
        return len(self.qpos_frames)

    @property
    def has_episode(self) -> bool:
        return self.frame_count > 0

    def to_motion_data(self, fps: int) -> dict:
        if not self.has_episode:
            raise ValueError("No recorded frames available to export.")
        qpos = np.asarray(self.qpos_frames)
        root_pos = qpos[:, :3].copy()
        root_rot = qpos[:, 3:7].copy()[:, [1, 2, 3, 0]]
        dof_pos = qpos[:, 7:].copy()
        return {
            "fps": fps,
            "root_pos": root_pos,
            "root_rot": root_rot,
            "dof_pos": dof_pos,
            "local_body_pos": None,
            "link_body_list": None,
        }

    def to_metadata(self, robot: str, actual_human_height: float, fps: int) -> dict:
        duration_sec = float(self.frame_count) / float(fps) if fps > 0 else 0.0
        return {
            "robot": robot,
            "src_human": "xrobot",
            "actual_human_height": float(actual_human_height),
            "frame_count": int(self.frame_count),
            "fps": int(fps),
            "duration_sec": duration_sec,
            "start_timestamp_ns": int(self.timestamps_ns[0]) if self.timestamps_ns else None,
            "end_timestamp_ns": int(self.timestamps_ns[-1]) if self.timestamps_ns else None,
        }
