import argparse
import json
import pickle
import time

import numpy as np
from rich import print

from general_motion_retargeting import GeneralMotionRetargeting as GMR
from general_motion_retargeting import RobotMotionViewer, XRobotStreamer
from general_motion_retargeting.params import IK_CONFIG_DICT
from live_record_controls import (
    ButtonEdgeDetector,
    LiveEpisodeBuffer,
    build_episode_paths,
    make_episode_stem,
)


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
    parser.add_argument(
        "--root_z_comp",
        type=float,
        default=0.0,
        help="Additive root Z compensation (meters) applied to retargeted qpos.",
    )
    parser.add_argument(
        "--record_with_controller",
        action="store_true",
        help="Enable controller-button recording during live stream.",
    )
    parser.add_argument(
        "--session_dir",
        type=str,
        default="converted_motions/pico_live",
        help="Folder to save recorded live episodes.",
    )
    parser.add_argument(
        "--save_on_exit",
        action="store_true",
        help="Auto-save current buffered episode when exiting with Ctrl+C.",
    )
    return parser.parse_args()


def save_recorded_episode(recorder, args, episode_index):
    stem = make_episode_stem(args.robot, episode_index)
    pkl_path, meta_path = build_episode_paths(args.session_dir, stem)

    motion_data = recorder.to_motion_data(fps=args.target_fps)
    metadata = recorder.to_metadata(
        robot=args.robot,
        actual_human_height=args.actual_human_height,
        fps=args.target_fps,
    )
    metadata["record_controls"] = {
        "start_stop": "RightController.key_one (A)",
        "save": "RightController.key_two (B)",
        "discard": "LeftController.key_two (Y)",
    }

    with pkl_path.open("wb") as file:
        pickle.dump(motion_data, file)
    with meta_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print(f"[record] Saved {recorder.frame_count} frames -> {pkl_path}")
    print(f"[record] Metadata -> {meta_path}")
    recorder.discard()
    return episode_index + 1


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
    button_detector = ButtonEdgeDetector()
    recorder = LiveEpisodeBuffer()
    episode_index = 1

    if args.record_with_controller:
        print("[record] Controller recording enabled:")
        print("  - A (right key_one): start/stop episode")
        print("  - B (right key_two): save buffered episode")
        print("  - Y (left key_two): discard buffered episode")

    try:
        while True:
            body_pose_dict, _, _, controller_data, _ = streamer.get_current_frame()
            if body_pose_dict is None:
                time.sleep(0.01)
                continue

            qpos = retarget.retarget(
                body_pose_dict,
                offset_to_ground=not args.no_offset_to_ground,
            )
            if args.root_z_comp != 0.0:
                qpos[2] += args.root_z_comp

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

            if args.record_with_controller:
                timestamp_ns = None
                if isinstance(controller_data, dict):
                    timestamp_ns = controller_data.get("timestamp")

                if button_detector.rising_edge(controller_data, "RightController", "key_one"):
                    if recorder.is_recording:
                        recorder.stop()
                        print(
                            f"[record] Episode stopped ({recorder.frame_count} frames). "
                            "Press B to save or Y to discard."
                        )
                    else:
                        recorder.start()
                        print("[record] Episode started.")

                if recorder.is_recording:
                    recorder.append(qpos, timestamp_ns=timestamp_ns)

                if button_detector.rising_edge(controller_data, "RightController", "key_two"):
                    if recorder.is_recording:
                        recorder.stop()
                    if recorder.has_episode:
                        episode_index = save_recorded_episode(recorder, args, episode_index)
                    else:
                        print("[record] No buffered episode to save.")

                if button_detector.rising_edge(controller_data, "LeftController", "key_two"):
                    if recorder.is_recording or recorder.has_episode:
                        recorder.discard()
                        print("[record] Buffered episode discarded.")
                    else:
                        print("[record] No buffered episode to discard.")

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
        if args.record_with_controller and args.save_on_exit:
            if recorder.is_recording:
                recorder.stop()
            if recorder.has_episode:
                episode_index = save_recorded_episode(recorder, args, episode_index)
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
