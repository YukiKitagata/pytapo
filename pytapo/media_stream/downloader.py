from pytapo.media_stream.convert import Convert
from pytapo import Tapo
from datetime import datetime
import json


class Downloader:
    def __init__(
        self, tapo: Tapo, startTime: int, endTime: int, outputDirectory="./", padding=5
    ):
        self.tapo = tapo
        self.startTime = startTime
        self.endTime = endTime
        self.padding = padding
        self.outputDirectory = outputDirectory

    async def download(self):
        convert = Convert()
        mediaSession = self.tapo.getMediaSession()
        async with mediaSession:
            payload = {
                "type": "request",
                "seq": 1,
                "params": {
                    "playback": {
                        "client_id": self.tapo.getUserID(),
                        "channels": [0, 1],
                        "scale": "1/1",
                        "start_time": str(self.startTime),
                        "end_time": str(self.endTime),
                        "event_type": [1, 2],
                    },
                    "method": "get",
                },
            }

            payload = json.dumps(payload)
            dataChunks = 0
            date = datetime.utcfromtimestamp(int(self.startTime)).strftime(
                "%Y-%m-%d %H_%M_%S"
            )
            segmentLength = self.endTime - self.startTime
            fileName = self.outputDirectory + str(date) + ".mp4"
            currentAction = "Downloading"
            async for resp in mediaSession.transceive(payload):
                if resp.mimetype == "video/mp2t":
                    dataChunks += 1
                    convert.write(resp.plaintext)
                    detectedLength = convert.getLength()

                    yield {
                        "currentAction": currentAction,
                        "fileName": fileName,
                        "progress": convert.getLength(),
                        "total": segmentLength,
                    }
                    if (
                        detectedLength
                        > segmentLength + self.padding
                        # > 10  # temp
                    ):
                        currentAction = "Converting"
                        yield {
                            "currentAction": currentAction,
                            "fileName": fileName,
                            "progress": convert.getLength(),
                            "total": segmentLength,
                        }
                        convert.save(fileName, segmentLength, "ffmpeg")