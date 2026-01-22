import os

import pytest

# This test opens an interactive Matplotlib window and is primarily meant for manual, local verification.
# Skip by default unless explicitly enabled.
if os.environ.get("POSELIB_RUN_PLOTTER_TESTS") != "1":
    pytest.skip(
        "Skipping interactive plotter test (set POSELIB_RUN_PLOTTER_TESTS=1 to enable).",
        allow_module_level=True,
    )

from typing import cast

import matplotlib.pyplot as plt
import numpy as np

from ..core import BasePlotterTask, BasePlotterTasks
from ..plt_plotter import Matplotlib3DPlotter
from ..simple_plotter_tasks import Draw3DDots, Draw3DLines

task = Draw3DLines(task_name="test", 
    lines=np.array([[[0, 0, 0], [0, 0, 1]], [[0, 1, 1], [0, 1, 0]]]), color="blue")
task2 = Draw3DDots(task_name="test2", 
    dots=np.array([[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]]), color="red")
task3 = BasePlotterTasks([task, task2])
plotter = Matplotlib3DPlotter(cast(BasePlotterTask, task3))
plt.show()
