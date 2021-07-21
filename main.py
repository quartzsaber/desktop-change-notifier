import cv2
import time
import numpy as np

from pynotifier import Notification
from mss import mss


def select_region(img):
    hover = np.zeros(2, dtype=np.int32)
    regions = []
    
    def mouse_cb(event, x, y, flags, params):
        regions, hover = params
        x = int(x / 0.75)
        y = int(y / 0.75)
        if event == cv2.EVENT_MOUSEMOVE:
            hover[0] = x
            hover[1] = y
        elif event == cv2.EVENT_LBUTTONDOWN:
            regions.append([x, y])
    
    img_scaled = cv2.resize(img, None, fx=0.75, fy=0.75)
    cv2.imshow('select_region', img_scaled)
    
    cv2.setMouseCallback('select_region', mouse_cb, param=(regions, hover))
    
    while True:
        overlay = img_scaled.copy()
        
        now_regions = [[int(y * 0.75) for y in x] for x in regions]
        if len(now_regions) % 2 != 0:
            now_regions.append([int(hover[0] * 0.75), int(hover[1] * 0.75)])
        for i in range(0, len(now_regions), 2):
            cv2.rectangle(overlay, now_regions[i], now_regions[i+1], (0, 255, 0), 2)
        
        cv2.imshow('select_region', overlay)
        
        if cv2.waitKey(1) & 0xff == ord('q'):
            break
    
    cv2.destroyWindow('select_region')
    
    if len(regions) % 2 != 0:
        regions = regions[:-1]
    
    mask = np.zeros((img.shape[0], img.shape[1], 1), dtype='uint8')
    
    for x1, y1, x2, y2 in (regions[x] + regions[x+1] for x in range(0, len(regions), 2)):
        cv2.rectangle(mask, [x1, y1], [x2, y2], (1, 1, 1), -1)
    
    return mask


def notify_change():
    import winsound
    winsound.Beep(880, 1000)


def notify_crash():
    Notification(
    	title='Crash alert',
        description='Desktop Change Notifier app has crashed',
        duration=3,
        urgency='normal'
    ).send()
    time.sleep(3)


if __name__ == '__main__':
    try:
        with mss() as sct:
            mon = sct.monitors[0]
            
            sct.grab(mon)
            time.sleep(0.1)
            
            img_ref = np.array(sct.grab(mon))
            mask = select_region(img_ref)
            mask = np.broadcast_to(mask, img_ref.shape)
            img_ref_masked = img_ref * mask
            
            sct.grab(mon)
            time.sleep(0.1)
            
            time_old = time.time()
            
            # On Windows 10 21H1 (19043), loop below takes 0.12 seconds per iteration.
            # Could be improved by using a better capture method (e.g. Desktop Duplication API)
            while True:
                img = np.array(sct.grab(mon))
                img *= mask
                if np.any(img != img_ref_masked):
                    notify_change()
                    break
    except:
        notify_crash()
        raise
