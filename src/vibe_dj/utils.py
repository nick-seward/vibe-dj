import os
import math
from mutagen import File as MutagenFile

def get_duration(file_path: str) -> int | None:
    try:
        audio = MutagenFile(file_path)
        if audio and audio.info:
            return int(math.ceil(audio.info.length))
    except Exception:
        pass
    return None
