import os, sys, time, asyncio
from telegram import Bot
from rsudp import printM, printW, printE, helpers
import rsudp.raspberryshake as rs
from rsudp.test import TEST

class Telegrammer(rs.ConsumerThread):
    def __init__(self, token, chat_id, testing=False,
                 q=False, send_images=False, extra_text=False,
                 sender='Telegram'):
        super().__init__()
        self.queue = q
        self.sender = sender
        self.alive = True
        self.send_images = send_images
        self.token = token
        self.chat_id = chat_id
        self.testing = testing
        self.fmt = '%Y-%m-%d %H:%M:%S.%f'
        self.region = f' - region: {rs.region.title()}' if rs.region else ''
        self.extra_text = helpers.resolve_extra_text(extra_text, max_len=4096, sender=self.sender)

        self.telegram = None
        if not self.testing:
            self.telegram = Bot(token=self.token)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.livelink = f'live feed ➡️ https://stationview.raspberryshake.org/#?net={rs.net}&sta={rs.stn}'
        self.message0 = f'(Raspberry Shake station {rs.net}.{rs.stn}{self.region}) Event detected at'
        self.last_message = False

        printM('Starting.', self.sender)

    def getq(self):
        d = self.queue.get()
        self.queue.task_done()
        if 'TERM' in str(d):
            self.alive = False
            printM('Exiting.', self.sender)
            self.loop.stop()
            self.loop.close()
            sys.exit()
        else:
            return d

    async def _when_alarm(self, d):
        event_time = helpers.fsec(helpers.get_msg_time(d))
        self.last_event_str = f'{event_time.strftime(self.fmt)[:22]}'
        message = f'{self.message0} {self.last_event_str} UTC{self.extra_text} - {self.livelink}'
        printM('Sending alert...', sender=self.sender)
        printM(f'Telegram message: {message}', sender=self.sender)

        try:
            if not self.testing:
                await self.telegram.send_message(chat_id=self.chat_id, text=message)
            else:
                TEST['c_telegram'][1] = True
        except Exception as e:
            printE(f'Could not send alert - {e}', sender=self.sender)
            try:
                printE('Waiting 5 seconds and trying to send again...', sender=self.sender, spaces=True)
                time.sleep(5)
                if not self.testing:
                    await self.telegram.send_message(chat_id=self.chat_id, text=message)
                else:
                    TEST['c_telegram'][1] = False
            except Exception as e2:
                printE(f'Final failure to send alert - {e2}', sender=self.sender)

        self.last_message = message

    async def _when_img(self, d):
        if not self.send_images:
            return

        imgpath = helpers.get_msg_path(d)
        if not os.path.exists(imgpath):
            printW(f'Could not find image: {imgpath}', sender=self.sender)
            return

        try:
            with open(imgpath, 'rb') as image:
                printM(f'Uploading image to Telegram: {imgpath}', sender=self.sender)
                if not self.testing:
                    await self.telegram.send_photo(chat_id=self.chat_id, photo=image)
                    printM('Sent image', sender=self.sender)
                else:
                    printM(f'Image ready to send - {imgpath}', sender=self.sender)
                    TEST['c_telegramimg'][1] = True
        except Exception as e:
            printE(f'Could not send image - {e}', sender=self.sender)
            try:
                time.sleep(5)
                with open(imgpath, 'rb') as image:
                    printM(f'Retrying upload of image: {imgpath}', sender=self.sender)
                    await self.telegram.send_photo(chat_id=self.chat_id, photo=image)
                    printM('Sent image (retry)', sender=self.sender)
            except Exception as e2:
                printE(f'Final failure to send image - {e2}', sender=self.sender)

    def run(self):
        while True:
            d = self.getq()

            if 'ALARM' in str(d):
                self.loop.run_until_complete(self._when_alarm(d))

            elif 'IMGPATH' in str(d):
                try:
                    self.loop.run_until_complete(asyncio.wait_for(self._when_img(d), timeout=5))
                except asyncio.TimeoutError:
                    printE('Image send timed out.', sender=self.sender)
