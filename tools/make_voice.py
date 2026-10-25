"""Record every spoken phrase with a neural voice and embed it in happy-farm.html.
Run from the project folder: python tools/make_voice.py [--voice en-US-JennyNeural] [--rate=-10%]"""
import argparse, asyncio, base64, json, os, re, sys, tempfile
import edge_tts

# keep in sync with allPhrases() in happy-farm.html (the self-test catches drift)
PHRASES = [
    "Hello Elaina!", "Let's play!", "Animals", "Bubbles", "Shapes",
    "Cow. Moooo!", "Pig. Oink oink!", "Duck. Quack!", "Sheep. Baaa!", "Cat. Meow!", "Dog. Woof woof!",
    "Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Pink",
    "Yay! Good job!",
    "Circle", "Square", "Triangle", "Star", "Heart",
    "Circle! Well done!", "Square! Well done!", "Triangle! Well done!", "Star! Well done!", "Heart! Well done!",
    "Hooray Elaina!", "Hooray!",
]
BEGIN, END = "/* VOICE-CLIPS:BEGIN */", "/* VOICE-CLIPS:END */"

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="en-US-JennyNeural")
    ap.add_argument("--rate", default="-10%")
    a = ap.parse_args()
    html = open("happy-farm.html", encoding="utf-8").read()
    if BEGIN not in html or END not in html:
        sys.exit("markers not found in happy-farm.html")
    clips = {}
    with tempfile.TemporaryDirectory() as d:
        for t in PHRASES:
            f = os.path.join(d, "c.mp3")
            await edge_tts.Communicate(t, a.voice, rate=a.rate).save(f)
            clips[t] = base64.b64encode(open(f, "rb").read()).decode()
    line = "const VOICE_CLIPS = " + json.dumps(clips, ensure_ascii=False) + ";"
    i, j = html.index(BEGIN) + len(BEGIN), html.index(END)
    html = html[:i] + "\n" + line + "\n" + html[j:]
    open("happy-farm.html", "w", encoding="utf-8", newline="").write(html)
    print(f"{len(clips)} clips, happy-farm.html is {os.path.getsize('happy-farm.html')} bytes")

asyncio.run(main())
