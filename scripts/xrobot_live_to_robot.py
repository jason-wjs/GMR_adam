import argparse
import time

import numpy as np
from rich import print

from general_motion_retargeting import GeneralMotionRetargeting as GMR
from general_motion_retargeting import RobotMotionViewer, XRobotStreamer
from general_motion_retargeting.params import IK_CONFIG_DICT


def parse_args():
    xrobot_targets = sorted(IK_CONFIG_DICT.get("xrobot", {}).keys())
    if not xrobot_targets:
        raise ValueError("No xrobot targets found in IK_CONFIG_DICT.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--robot",
        choices=xrobot_targets,
        default="adam_pro_29dof" if "adam_pro_29dof" in xrobot_targets else xrobot_targets[0],
        help="Target robot for xrobot (PICO) retargeting.",
    )
    parser.add_argument(
        "--actual_human_height",
        type=float,
        default=1.6,
        help="Actual human height for retargeting scale (PICO tends to underestimate).",
    )
    parser.add_argument(
        "--target_fps",
        type=int,
        default=30,
        help="Viewer target FPS.",
    )
    parser.add_argument(
        "--show_human",
        action="store_true",
        help="Visualize human frames alongside robot.",
    )
    parser.add_argument(
        "--show_human_names",
        action="store_true",
        help="Show human joint names in visualization.",
    )
    parser.add_argument(
        "--human_point_scale",
        type=float,
        default=0.1,
        help="Scale for human point visualization.",
    )
    parser.add_argument(
        "--human_offset",
        type=float,
        nargs=3,
        default=[0.0, 0.0, 0.0],
        help="XYZ offset for human visualization.",
    )
    parser.add_argument(
        "--no_rate_limit",
        action="store_true",
        help="Disable rate limiting (render as fast as possible).",
    )
    parser.add_argument(
        "--no_follow_camera",
        action="store_true",
        help="Disable camera follow.",
    )
    parser.add_argument(
        "--no_offset_to_ground",
        action="store_true",
        help="Disable ground offset in retargeting.",
    )
    parser.add_argument(
        "--measure_fps",
        action="store_true",
        help="Print simple FPS stats.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if XRobotStreamer is None:
        print("[bold red]XRobotStreamer unavailable. Install xrobotoolkit_sdk first.[/bold red]")
        return

    print(f"[bold green]Starting xrobot live retargeting to {args.robot}[/bold green]")
    print("Press Ctrl+C to exit.")

    streamer = XRobotStreamer()
    retarget = GMR(
        src_human="xrobot",
        tgt_robot=args.robot,
        actual_human_height=args.actual_human_height,
    )
    viewer = RobotMotionViewer(
        robot_type=args.robot,
        motion_fps=args.target_fps,
        transparent_robot=0,
    )

    last_time = time.time()
    frame_count = 0

    try:
        while True:
            body_pose_dict, left_hand, right_hand, controller_data, headset_pose = streamer.get_current_frame()
            if body_pose_dict is None:
                time.sleep(0.01)
                continue

            qpos = retarget.retarget(
                body_pose_dict,
                offset_to_ground=not args.no_offset_to_ground,
            )

            viewer.step(
                root_pos=qpos[:3],
                root_rot=qpos[3:7],
                dof_pos=qpos[7:],
                human_motion_data=body_pose_dict if args.show_human else None,
                show_human_body_name=args.show_human_names,
                human_point_scale=args.human_point_scale,
                human_pos_offset=np.array(args.human_offset),
                rate_limit=not args.no_rate_limit,
                follow_camera=not args.no_follow_camera,
            )

            if args.measure_fps:
                frame_count += 1
                now = time.time()
                if now - last_time >= 1.0:
                    fps = frame_count / (now - last_time)
                    print(f"[xrobot_live] FPS: {fps:.1f}")
                    frame_count = 0
                    last_time = now
    except KeyboardInterrupt:
        print("\n[bold yellow]Exiting...[/bold yellow]")
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
