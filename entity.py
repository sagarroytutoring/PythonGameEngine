from abc import ABC, abstractmethod
import re
import glob
import os


class Entity(ABC):
    def __init__(self, x=0, y=0, hitwidth=0, hitheight=0):
        self.x = x
        self.y = y
        self.hitheight = hitheight
        self.hitwidth = hitwidth


class AnimatedEntity(ABC, Entity):
    def __init__(self, folderpath, x=0, y=0, hitwidth=0, hitheight=0, file_ext="gif"):
        super().__init__(x, y, hitwidth, hitheight)

        # Find all the frames in the correct folder
        foldername = os.path.dirname(folderpath)
        frame_dict = {}
        for f in glob.glob(fr"{folderpath}/*.{file_ext}"):
            match = re.fullmatch(fr"{folderpath}/{foldername}(\d+)\.gif", f)
            if match is None:
                continue
            frame_dict[int(match[1])] = f

        if not frame_dict:
            raise ValueError(f"No frames provided in folder {foldername}")

        # Store frames in list
        self.frames = []
        last_frame = max(frame_dict)
        for i in range(last_frame + 1):
            if i not in frame_dict:
                raise ValueError(f"Missing frames for {foldername}")
            self.frames.append(frame_dict[i])
