import importlib.util
import sys
from pathlib import Path

from PIL import Image


def load_select_video_keyframes():
    script = Path(__file__).resolve().parents[1] / "scripts" / "select_video_keyframes.py"
    sys.path.insert(0, str(script.parent))
    spec = importlib.util.spec_from_file_location("select_video_keyframes", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (32, 24), color).save(path)


def test_scene_candidate_command_combines_scene_changes_with_density_floor():
    module = load_select_video_keyframes()

    command = module.build_extract_command(
        Path("lesson.mp4"),
        Path("frames") / "frame_%04d.jpg",
        mode="scene",
        fps=25.0,
        interval_seconds=2,
        width=768,
        scene_threshold=0.3,
    )

    filter_index = command.index("-vf") + 1
    assert command[filter_index] == "select='gt(scene,0.3)+not(mod(n,50))',showinfo,scale=768:-1"
    assert "-vsync" in command


def test_showinfo_timestamps_are_mapped_to_frame_names():
    module = load_select_video_keyframes()

    stderr = """
    [Parsed_showinfo_1 @ 0x123] n:   0 pts:  25000 pts_time:1.000 pos:0
    [Parsed_showinfo_1 @ 0x123] n:   1 pts:  62500 pts_time:2.500 pos:0
    """

    frames = [Path("frame_0001.jpg"), Path("frame_0002.jpg")]

    assert module.map_showinfo_timestamps(frames, stderr) == {
        "frame_0001.jpg": 1.0,
        "frame_0002.jpg": 2.5,
    }


def test_deduplicate_candidates_uses_recent_kept_window_and_preserves_timestamps(tmp_path):
    module = load_select_video_keyframes()

    write_image(tmp_path / "frame_0001.jpg", (255, 0, 0))
    write_image(tmp_path / "frame_0002.jpg", (254, 0, 0))
    write_image(tmp_path / "frame_0003.jpg", (0, 0, 255))
    write_image(tmp_path / "frame_0004.jpg", (253, 0, 0))
    timestamps = {
        "frame_0001.jpg": 1.0,
        "frame_0002.jpg": 2.0,
        "frame_0003.jpg": 3.0,
        "frame_0004.jpg": 4.0,
    }

    result = module.deduplicate_candidates(
        tmp_path,
        timestamps,
        threshold=8.0,
        window=2,
        max_candidates=0,
    )

    assert result["candidate_count"] == 2
    assert sorted(path.name for path in tmp_path.glob("*.jpg")) == ["frame_0001.jpg", "frame_0002.jpg"]
    assert result["timestamp_map"] == {
        "frame_0001.jpg": 1.0,
        "frame_0002.jpg": 3.0,
    }
    assert [record["kept"] for record in result["dedup_records"]] == [True, False, True, False]


def test_deduplicate_candidates_uniformly_thins_when_over_cap(tmp_path):
    module = load_select_video_keyframes()

    timestamps = {}
    for index in range(1, 6):
        name = f"frame_{index:04d}.jpg"
        write_image(tmp_path / name, (index * 30, 0, 255 - index * 30))
        timestamps[name] = float(index)

    result = module.deduplicate_candidates(
        tmp_path,
        timestamps,
        threshold=0.1,
        window=1,
        max_candidates=3,
    )

    assert result["candidate_count"] == 3
    assert result["raw_candidate_count"] == 5
    assert result["timestamp_map"] == {
        "frame_0001.jpg": 1.0,
        "frame_0002.jpg": 2.0,
        "frame_0003.jpg": 4.0,
    }
