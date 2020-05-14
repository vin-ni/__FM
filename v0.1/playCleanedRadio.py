# this is a really basic player
# there's a lot of improvement needed, such as seamless playing and performant audio lookup

import time, vlc, os, glob
import re

instance = vlc.Instance('--input-repeat=-1', '--fullscreen', '--mouse-hide-timeout=0')
globalIndex = 0
globalPlaylist = []

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def updatePlaylistLength():
    global globalPlaylist
    globalPlaylist = []
    for root, dirs, files in os.walk('result/'):
        globalPlaylist += glob.glob(os.path.join(root, '*.mp3'))
    globalPlaylist.sort(key=natural_keys)



def playRadio(index):
    global globalPlaylist
    player=instance.media_player_new()
    media=instance.media_new(globalPlaylist[index])

    media.get_mrl()
    player.set_media(media)
    player.play()
    playing = set([1,2,3,4])
    time.sleep(1)
    duration = player.get_length() / 1000
    #mm, ss = divmod(duration, 60)

    updatePlaylistLength()

    while True:
        global globalIndex
        state = player.get_state()
        if state not in playing:
            globalIndex += 1
            playRadio(globalIndex)
            break
        continue

updatePlaylistLength()
#print(globalPlaylist)
playRadio(globalIndex)

## play one sound
# def Sound(sound):
#     vlc_instance = vlc.Instance()
#     player = vlc_instance.media_player_new()
#     media = vlc_instance.media_new(sound)
#     player.set_media(media)
#     player.play()
#     time.sleep(1.5)
#     duration = player.get_length() / 1000
#     time.sleep(duration)
# Sound('result/stream8.mp3')

