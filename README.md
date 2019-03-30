# PPP
Plex Playlist Pusher (Python Re-write)

*Looking for the original Bash version? Find it [here](https://github.com/XDGFX/PPP/tree/master)*

A simple Python 3 script used to automatically:
- load .m3u playlists from a local directory (maybe your MusicBee library... **Can't be the same directory as your PPP installation!**)
- load music playlists from Plex
- compare the two, merging any new tracks or entire playlists
- push the updated playlists back to Plex using the Plex Playlist API (https://forums.plex.tv/t/can-plexamp-read-and-use-m3u-playlists/234179/21)
- copy the updated playlists back to your local directory

This will keep Plex playlists and local playlists synchronised.
If you want to delete a playlist or song from a playlist, it must be removed from BOTH local and Plex playlists.

### Usage instructions
1. Install Python 3.X if you haven't already
2. Open PPP.py with a text editor
3. Change the below variables to suit your use case
4. Save and run the file

### Variables
`server_url` the url of your Plex server, as seen by whatever you're running PPP on [e.g. 192.168.1.96:32400]

`plex_token` find it here: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/ [e.g. P6X4rFdFhcTssbA6pXoT]

`local_playlists` path to the local playlists you want to use, relative to whatever you're running PPP on [e.g. /mnt/Playlists]

`install directory` path to your PPP install directory, relative to your PLEX MACHINE (which may be different to the machine you run PPP on) [e.g. D:\\\\Media\\\\PPP]

`section_id` the library section which contains the music you are adding to playlists (Google will help you find it) [e.g. 11]

`local_prepend` see below

`plex_prepend` see below

#### EXAMPLE LOCAL_PLAYLIST

> \\\\uluru\Uluru\Media\Music\Andrew Huang\Love Is Real\Love Is Real.mp3
>
> \\\\uluru\Uluru\Media\Music\Ben Howard\Noonday Dream\A Boat To An Island On The Wall.mp3
>
> \\\\uluru\Uluru\Media\Music\Bibio\PHANTOM BRICKWORKS\PHANTOM BRICKWORKS.mp3


#### EXAMPLE PLEX_PLAYLIST (if exported in m3u format)

> D:\Media\Music\Andrew Huang\Love Is Real\Love Is Real.mp3
>
> D:\Media\Music\Ben Howard\Noonday Dream\A Boat To An Island On The Wall.mp3
>
> D:\Media\Music\Bibio\PHANTOM BRICKWORKS\PHANTOM BRICKWORKS.mp3


In the examples above, `local_prepend` is *\\\\\\\\uluru\\\\Uluru\\\\* and `plex_prepend` is *D:\\\\*

**Why are there so many backslashes?**
You need to double any backslash, because normally it's a special 'escape character' which would break the code. You need to 'escape' the 'escape character' (https://stackoverflow.com/questions/19095796/how-to-print-backslash-with-python)

**Want to run this automatically every X amount of time?**
Use [crontab](https://www.raspberrypi.org/documentation/linux/usage/cron.md). You may need to apply [this fix](https://www.digitalocean.com/community/questions/unable-to-execute-a-python-script-via-crontab-but-can-execute-it-manually-what-gives).

Example crontab:

`* * * * * cd /path/to/PPP && /usr/bin/python3 /path/to/PPP/PPP.py >> /path/to/PPP/PPP.log`
