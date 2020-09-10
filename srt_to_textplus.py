#!/usr/bin/env python

import srt
import time
from pprint import pprint
import textwrap
import DaVinciResolveScript as dvr

PROJECT_NAME = "Hello World"
TIMELINE_NAME = "Timeline 1"
COMP_NAME = "Fusion Composition"
FRAME_RATE = 30
FRAME_HEIGHT = 1080
FRAME_WIDTH = 1080
FONT = "Noto Sans"
FONT_SIZE = 0.09
LINE_SPACING = 1.25
LINE_WRAP_CHARS = 32
SHADER2_NAME = "Green Outline"
SHADER2_SHAPE = 2
SHADER2_EXTEND_H = 2
SHADER2_EXTEND_V = 0.5
SHADER2_COLOUR_HEX = "#53e2c4"
SHADER2_ALPHA = 0.95
ANIMATION_DURATION_FRAMES = 5

def HexToFloats(h):
    '''Takes a hex rgb string (e.g. #ffffff) and returns an RGB tuple (float, float, float).'''
    return tuple(int(h[i:i + 2], 16) / 255. for i in (1, 3, 5)) # skip '#'

def TimestampToFrames(t, f):
    return round(t.total_seconds() * f)

# Load davinci script module
resolve = dvr.scriptapp('Resolve')
fusion = dvr.scriptapp('Fusion')

# Open subtitle file
fp = open("subtitle.srt")
fs = fp.read().decode('utf-8-sig')
subs = list(srt.parse(fs))

# Get subtitle duration
total_frames = TimestampToFrames(subs[-1].end, FRAME_RATE)

# Open Fusion 
resolve.OpenPage("Fusion")
composition = fusion.GetCurrentComp()
composition.Lock()
composition.SetPrefs(
        {
            "Comp.FrameFormat.Width"    :   FRAME_WIDTH,
            "Comp.FrameFormat.Height"   :   FRAME_HEIGHT,
            "Comp.FrameFormat.Rate"     :   FRAME_RATE,
            "Comp.Unsorted.GlobalEnd"   :   total_frames
        }
    )
composition.SetAttrs(
        {
            "COMPN_GlobalEnd" : total_frames,
            "COMPN_RenderEnd" : total_frames
        }
    )

# Generate subtitle TextPlus nodes
text_nodes = list()
background_colour = HexToFloats(SHADER2_COLOUR_HEX)

for sub in subs:
    line = composition.AddTool("TextPlus")
    line.StyledText = textwrap.fill(sub.content, width = LINE_WRAP_CHARS)
    line.Font = FONT
    line.LineSpacingClone = LINE_SPACING
    line.Enabled2 = 1
    line.Name2 = SHADER2_NAME
    line.ElementShape2 = SHADER2_SHAPE
    line.ExtendHorizontal2 = SHADER2_EXTEND_H
    line.ExtendVertical2 = SHADER2_EXTEND_V
    line.Red2 = background_colour[0]
    line.Green2 = background_colour[1]
    line.Blue2 = background_colour[2]
    line.Alpha2 = SHADER2_ALPHA

    # Animate line appearance
    line_start_frame = TimestampToFrames(sub.start, FRAME_RATE)
    animation_start_frame = line_start_frame - ANIMATION_DURATION_FRAMES
    if animation_start_frame < 0:
        animation_start_frame = 0

    animation_end_frame = TimestampToFrames(sub.end, FRAME_RATE)
    line_end_frame = animation_end_frame - ANIMATION_DURATION_FRAMES

    # Create animation path to define keyframes for TextPlus object, with unique path name
    line.Center = composition.Path("%d" % (animation_start_frame))
    line.Center[0] = [1.5, 0.5, 0.0]
    line.Center[animation_start_frame] = [1.5, 0.5, 0.0]
    line.Center[line_start_frame] = [0.5, 0.5, 0.0]
    line.Center[line_end_frame] = [0.5, 0.5, 0.0]
    line.Center[animation_end_frame] = [-0.5, 0.5, 0.0]
    line.Center[total_frames] = [-0.5, 0.5, 0.0]

    text_nodes.append(line)

# Merge TextPlus nodes
merge_nodes = list()

for i in range(1, len(text_nodes)):
    fg = text_nodes[i-1] if i == 1 else merge_nodes[i-2]
    bg = text_nodes[i]
    merge = composition.Merge({"Background": fg, "Foreground": bg})
    merge_nodes.append(merge)


composition.Unlock()
