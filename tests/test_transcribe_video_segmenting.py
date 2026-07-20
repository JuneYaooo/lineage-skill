import importlib.util
from pathlib import Path


def load_transcribe_video():
    script = Path(__file__).resolve().parents[1] / "scripts" / "transcribe_video.py"
    spec = importlib.util.spec_from_file_location("transcribe_video", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_transcribe_audio_segments_when_duration_exceeds_configured_seconds(tmp_path, monkeypatch):
    module = load_transcribe_video()
    audio = tmp_path / "lesson.mp3"
    audio.write_bytes(b"x" * 1024)

    calls = []

    monkeypatch.setenv("AUDIO_TRANSCRIBE_SEGMENT_SECONDS", "90")
    monkeypatch.setattr(module, "get_audio_duration", lambda path: 181.0)

    def fake_extract_audio_segment(audio_path, start, duration, output_path):
        calls.append((start, duration, Path(output_path).name))
        Path(output_path).write_bytes(b"segment")
        return True

    def fake_transcribe_audio_api(segment_path):
        return {
            "full_text": Path(segment_path).stem,
            "duration": 90.0,
        }

    monkeypatch.setattr(module, "extract_audio_segment", fake_extract_audio_segment)
    monkeypatch.setattr(module, "transcribe_audio_api", fake_transcribe_audio_api)

    result = module.transcribe_audio(str(audio), "lesson", temp_dir=str(tmp_path))

    assert [call[:2] for call in calls] == [(0.0, 90.0), (90.0, 90.0), (180.0, 1.0)]
    assert result["engine"].endswith("_segmented")
    assert len(result["segments"]) == 3


def test_transcribe_audio_keeps_direct_path_for_short_audio(tmp_path, monkeypatch):
    module = load_transcribe_video()
    audio = tmp_path / "short.mp3"
    audio.write_bytes(b"x" * 1024)

    monkeypatch.setenv("AUDIO_TRANSCRIBE_SEGMENT_SECONDS", "90")
    monkeypatch.setattr(module, "get_audio_duration", lambda path: 89.0)
    monkeypatch.setattr(
        module,
        "transcribe_audio_api",
        lambda path: {"full_text": "short text", "duration": 89.0},
    )

    result = module.transcribe_audio(str(audio), "short", temp_dir=str(tmp_path))

    assert result["full_text"] == "short text"


def test_transcribe_audio_splits_failed_segment_into_smaller_parts(tmp_path, monkeypatch):
    module = load_transcribe_video()
    audio = tmp_path / "lesson.mp3"
    audio.write_bytes(b"x" * 1024)

    extracted = []

    monkeypatch.setenv("AUDIO_TRANSCRIBE_SEGMENT_SECONDS", "60")
    monkeypatch.setenv("AUDIO_TRANSCRIBE_MIN_SEGMENT_SECONDS", "30")
    monkeypatch.setattr(module, "get_audio_duration", lambda path: 61.0)

    def fake_extract_audio_segment(audio_path, start, duration, output_path):
        extracted.append((start, duration, Path(output_path).stem))
        Path(output_path).write_bytes(b"segment")
        return True

    def fake_transcribe_audio_api(segment_path):
        stem = Path(segment_path).stem
        if stem == "lesson_segment_01":
            raise Exception("provider 500")
        return {
            "full_text": stem,
            "duration": 30.0,
        }

    monkeypatch.setattr(module, "extract_audio_segment", fake_extract_audio_segment)
    monkeypatch.setattr(module, "transcribe_audio_api", fake_transcribe_audio_api)

    result = module.transcribe_audio(str(audio), "lesson", temp_dir=str(tmp_path))

    assert extracted[:3] == [
        (0.0, 60, "lesson_segment_01"),
        (0.0, 30.0, "lesson_segment_01a"),
        (30.0, 30.0, "lesson_segment_01b"),
    ]
    assert result["segments"][0]["start"] == 0.0
    assert result["segments"][1]["start"] == 30.0


def test_transcribe_audio_skips_tiny_tail_segment(tmp_path, monkeypatch):
    module = load_transcribe_video()
    audio = tmp_path / "lesson.mp3"
    audio.write_bytes(b"x" * 1024)

    extracted = []

    monkeypatch.setenv("AUDIO_TRANSCRIBE_SEGMENT_SECONDS", "30")
    monkeypatch.setenv("AUDIO_TRANSCRIBE_SKIP_TAIL_SECONDS", "1")
    monkeypatch.setattr(module, "get_audio_duration", lambda path: 60.2)

    def fake_extract_audio_segment(audio_path, start, duration, output_path):
        extracted.append((start, duration))
        Path(output_path).write_bytes(b"segment")
        return True

    def fake_transcribe_audio_api(segment_path):
        return {
            "full_text": Path(segment_path).stem,
            "duration": 30.0,
        }

    monkeypatch.setattr(module, "extract_audio_segment", fake_extract_audio_segment)
    monkeypatch.setattr(module, "transcribe_audio_api", fake_transcribe_audio_api)

    result = module.transcribe_audio(str(audio), "lesson", temp_dir=str(tmp_path))

    assert [duration for _, duration in extracted] == [30, 30]
    assert len(result["segments"]) == 2


def test_transcribe_audio_records_empty_min_segment(tmp_path, monkeypatch):
    module = load_transcribe_video()
    audio = tmp_path / "lesson.mp3"
    audio.write_bytes(b"x" * 1024)

    monkeypatch.setenv("AUDIO_TRANSCRIBE_ALLOW_EMPTY_SEGMENTS", "1")

    def fake_extract_audio_segment(audio_path, start, duration, output_path):
        Path(output_path).write_bytes(b"silence")
        return True

    def fake_transcribe_audio_api(segment_path):
        raise module.EmptyTranscriptionError("empty text")

    monkeypatch.setattr(module, "extract_audio_segment", fake_extract_audio_segment)
    monkeypatch.setattr(module, "transcribe_audio_api", fake_transcribe_audio_api)

    parts, segments = module.transcribe_audio_segment(
        str(audio),
        "lesson",
        str(tmp_path),
        "01",
        10.0,
        15.0,
        15,
    )

    assert parts == []
    assert segments == [{"start": 10.0, "end": 25.0, "text": "", "empty": True}]
