<p align="center">
  <img src="/branding/logo.png" alt="PPP">

  <b>Plex Playlist Pusher (Python Re-write)</b>

  <i>Looking for the original Bash version? Find it <a href="https://github.com/XDGFX/PPP/tree/master">here</a></i>
</p>

---

A simple Python 3 script used to automatically:
- load .m3u playlists from a local directory (maybe your MusicBee library... **Can't be the same directory as your PPP installation!**)
- load music playlists from Plex
- compare the two, merging any new tracks or entire playlists
- push the updated playlists back to Plex using the Plex Playlist API (https://forums.plex.tv/t/can-plexamp-read-and-use-m3u-playlists/234179/21)
- copy the updated playlists back to your local directory

This will keep Plex playlists and local playlists synchronised.
If you want to delete a playlist or song from a playlist, it must be removed from BOTH local and Plex playlists.

---

## Usage instructions
1. Install Python 3 if you haven't already
2. Download the latest release of PPP from [here](https://github.com/XDGFX/PPP/releases)
3. For first run, see [Setup](#Setup)
4. Run PPP with Python 3

```
usage: PPP.py [-h] [-setup] [-nobackups] [-retention n] [-nocleanup]

optional arguments:
  -h, --help    show this help message and exit
  -setup        Force-run the setup procedure
  -nobackups    Disable backup of local playlists completely!
  -retention n  Number of previous local playlist backups to keep (Default 10)
  -nocleanup    Disable removal of .tmp directory (for debugging only)
  ```
---

## Setup
PPP will guide you through a setup on first run, and attempt to help you find all required variables. 
- Variables are saved to variables.json
- If needed this can be edited manually

Alternatively rename `example-variables.json` to `variables.json` and edit the file manually.

---

## Automation 
#### Linux
Use [crontab](https://www.raspberrypi.org/documentation/linux/usage/cron.md). You may need to apply [this fix](https://www.digitalocean.com/community/questions/unable-to-execute-a-python-script-via-crontab-but-can-execute-it-manually-what-gives).

Example crontab:

`* * * * * cd /path/to/PPP && /usr/bin/python3 /path/to/PPP/PPP.py >> /path/to/PPP/PPP.log 2>&1`

#### Windows
Use task scheduler? I haven't tested it.

---

## Variables (Reference)
Running setup should help you find all these variables!

| VARIABLE | DESCRIPTION | EXAMPLE |
|---|---|---|
| `server_url` | the url of your Plex server, as seen by whatever you're running PPP on | `"http://192.168.1.100:32400"` |
| `check_ssl` | validate, or ignore SSL certificate ('"False"' for self signed https) | `"True"` |
| `plex_token` | find it [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) | `"A1B3c4bdHA3s8COTaE3l"` |
| `local_playlists` | path to the local playlists you want to use, relative to PPP | `"/mnt/Playlists"` |
| `install_directory` | path to PPP install directory, as seen by Plex (to allow uploading of new playlists) | `"/mnt/PPP"` |
| `section_id` | the library section which contains all your music (only one section is supported by the Plex API) | `"11"` |
| `local_prepend` | path to be ignored in local playlists | `"Z:\\Media\\Music\\"` |
| `plex_prepend` | path to be ignored in Plex playlists | `"/mnt/Media/Music"` |
| `local_convert` | only if local playlists are in a different directory format to your PPP machine | `"w2u"` |
| `plex_convert` | only if you Plex playlists are in a different directory format to your PPP machine | `False` |


    --- EXAMPLE LOCAL_PLAYLIST ---
    Z:\Media\Music\Andrew Huang\Love Is Real\Love Is Real.mp3
    Z:\Media\Music\Ben Howard\Noonday Dream\A Boat To An Island On The Wall.mp3
    Z:\Media\Music\Bibio\PHANTOM BRICKWORKS\PHANTOM BRICKWORKS.mp3

    --- EXAMPLE PLEX_PLAYLIST ---
    /mnt/media/Music/Andrew Huang/Love Is Real/Love Is Real.mp3
    /mnt/media/Music/Ben Howard/Noonday Dream/A Boat To An Island On The Wall.mp3
    /mnt/media/Music/Bibio/PHANTOM BRICKWORKS/PHANTOM BRICKWORKS.mp3


In the examples above, `local_prepend` is `"Z:\\Media\\Music\\"` and `plex_prepend` is `"/mnt/Media/Music"`

In this example, PPP is running on a machine which uses UNIX paths (/ not \\), and so `local_convert` is `"w2u"` - which means Windows paths are converted to UNIX paths.

If running PPP on Windows and your playlist paths are UNIX, use `"u2w"`, and if both paths are the same format use `false`.

**Why are there so many backslashes?**
You need to double any backslash, because normally it's a special 'escape character' which would break the code. You need to 'escape' the 'escape character' (https://stackoverflow.com/questions/19095796/how-to-print-backslash-with-python)
