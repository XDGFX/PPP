# --- PPP (Plex Playlist Pusher) v3.0.0 ---
# Synchronises playlists between local files (.m3u) and Plex playlists.
# If there are differences between local and Plex playlists, both will be
# merged and duplicates deleted; meaning tracks can be added on one and
# updated on both... but must be deleted on BOTH to remove completely
# (the same goes for new playlists).

# XDGFX 2019

# 17/03/19 Started working on script
# 19/03/19 Original v2.0 Release
# 20/03/19 v2.1 Updated to use tempfile module temporary directory
# 22/03/19 v2.1.1 General improvements and bug fixes
# 23/03/19 v2.1.2 Fixed v2.1 and v2.1.1 releases, no longer using tempfile
# 30/03/19 v2.1.3 Added timestamp and improved character support
# 20/12/19 v3.0.0 MAJOR REWRITE: Added setup procedure and UNIX / Windows compatibility

from datetime import datetime                # for timestamp
import requests                              # HTTP POST requests
from collections import OrderedDict          # url ordering
import io                                    # character encoding
import os                                    # for folder and file management
import shutil                                # for deleting files
import argparse                              # for arguments
from xml.etree import ElementTree            # for xml
import re                                    # for verifying input variables
import json                                  # for saving of variables

vers = "v3.0.0"

# Uses GNU General Public License

# Import modules


# --- FUNCTIONS ---

def br():
    print("\n------\n")


def plexSections(server_url, plex_token):
    try:
        print("Requesting section info from Plex...")
        url = server_url + "/library/sections/all?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30)

        if resp.status_code == 200:
            print("Requesting of section info was successful.")
            root = ElementTree.fromstring(resp.text)
            print("ID: SECTION")

            for document in root.findall("Directory"):
                if document.get('type') == "artist":
                    print(document.get('key') + ': ' +
                          document.get('title').strip())

    except Exception:
        print("ERROR: Issue encountered when attempting to list detailed sections info.")
        raise SystemExit


def plexPlaylistKeys(server_url, plex_token):
    try:
        print("Requesting playlists from Plex...")
        url = server_url + "/playlists/?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30)

        if resp.status_code == 200:
            print("Requesting of playlists was successful.")
            root = ElementTree.fromstring(resp.text)

            keys = []
            for document in root.findall("Playlist"):
                if document.get('smart') == "0" and document.get('playlistType') == "audio":
                    keys.append(document.get('key'))

            print("Found " + str(len(keys)) + " playlists.")

            return keys

    except Exception as e:
        print("ERROR: Issue encountered when attempting to list detailed sections info.")
        print("ERROR: %s", e)
        raise SystemExit


def plexPlaylist(server_url, plex_token, key):
    try:
        print("Requesting playlist data from Plex...")
        url = server_url + key + "?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30)

        if resp.status_code == 200:
            root = ElementTree.fromstring(resp.text)

            title = root.get("title")

            print("Found playlist: " + title)

            playlist = []
            for document in root.findall("Track"):
                playlist.append(document[0][0].get('file'))

            print("Found " + str(len(playlist)) + " songs.")

            return playlist

    except Exception as e:
        print("ERROR: Issue encountered when attempting to get Plex playlist.")
        print("ERROR: %s", e)
        raise SystemExit


def setupVariables():
    import getpass

    # Remove variables.json if it already exists
    if os.path.isfile('variables.json'):
        try:
            shutil.rmtree('variables.json')
        except Exception as e:
            print(
                "ERROR: I couldn't remove existing variables.json. Try deleting manually?")
            print(e)
            raise SystemExit

    print("It looks like you haven't run this script before!\nThe setup " +
          "process is now starting... \n \nIf you believe this is an error, please " +
          "check variables.py is present, and accessible by PPP.")

    br()

    # UNIX CHECK
    ppp_unix = True if not os.name == "nt" else False
    plex_convert = False
    local_convert = False

    print("It looks like your PPP machine uses %s paths",
          "UNIX" if ppp_unix else "Windows")

    br()

    # SERVER URL
    print("First things first... what is your Plex server URL, as seen by " +
          "PPP? It must include port, in the form '192.198.1.10:32400'")
    server_url = input("Please enter your server URL: ")

    if not re.match('(?:http|https)://', server_url):
        server_url = "http://" + server_url

    br()

    # Regex to check URL with port
    if re.compile("^(?:http|https)://[\\d.]+:\\d+$").match(server_url) is None:
        input("WARNING: Entered URL '" + server_url + "' does not appear to follow the correct format!\n" +
              "If you believe this is a mistake, press enter to continue... ")

        br()

    # PLEX TOKEN
    print("Next we need your Plex Token. You can find this by following these instructions: https://bit.ly/2p7RtOu")
    plex_token = getpass.getpass("Please enter your Plex Token: ")

    br()

    # Regex to check token
    if re.compile("^[A-Za-z1-9]+$").match(plex_token) is None:
        input("WARNING: Entered token '" + server_url + "' does not appear to follow the correct format!\n" +
              "If you believe this is a mistake, press enter to continue... ")

        br()

    # Fetch Plex music playlist keys
    keys = plexPlaylistKeys(server_url, plex_token)

    br()

    print("Fetching sample playlist to determine prepend...")
    playlist = plexPlaylist(server_url, plex_token, keys[0])

    plex_unix = playlist[0].startswith("/")

    print("It looks like your Plex machine uses %s paths",
          "UNIX" if plex_unix else "Windows")

    # Convert from Windows to UNIX paths
    if plex_unix != ppp_unix:

        print("Plex playlists are not in PPP directory format!")
        print("Attempting to convert Plex directories to PPP machine format")

        if ppp_unix:
            plex_convert = "w2u"
            playlist = [track.replace("\\", "/") for track in playlist]
        else:
            plex_convert = "u2w"
            playlist = [track.replace("/", "\\") for track in playlist]

    plex_prepend = os.path.commonpath(playlist)
    print("Calculated Plex Prepend: " + plex_prepend)

    br()

    # LOCAL PLAYLISTS
    print("Now we need the location of your local playlists, as seen by PPP\n" +
          "There is no need to escape spaces or special characters.")
    local_playlists = input("Please enter your local playlists directory: ")

    br()

    # Look for playlists
    playlistsFound = False
    for root, _, files in os.walk(local_playlists):
        for file in files:
            if file.endswith('.m3u'):
                playlistsFound = True
                playlist = io.open(
                    os.path.join(root, file), 'r', encoding='utf8').read().splitlines()
                break

    if not playlistsFound:
        print("ERROR: We couldn't find any .m3u playlists!")
        input("If this is expected (i.e. you want to sync playlists from Plex) press enter to continue...")

    local_unix = playlist[0].startswith("/")

    print("It looks like your local playlists use %s paths",
          "UNIX" if local_unix else "Windows")

    # Convert from Windows to UNIX paths
    if local_unix != ppp_unix:

        print("Local playlists are not in PPP directory format!")
        print("Attempting to convert local directories to PPP machine format")

        if ppp_unix:
            local_convert = "w2u"
            playlist = [track.replace("\\", "/") for track in playlist]
        else:
            local_convert = "w2u"
            playlist = [track.replace("/", "\\") for track in playlist]

    local_prepend = os.path.commonpath(playlist)
    print("Calculated local Prepend: " + local_prepend)

    br()

    # INSTALL DIRECTORY
    print("Now we need your PPP install directory, as seen by Plex. \n" +
          "This is so Plex can access temporary playlists that will be saved " +
          "in this directory.")
    install_directory = input(
        "Please enter your PPP install directory, relative to Plex: ")

    br()

    # SECTION ID
    print("Your section ID is the library ID where you store all your music. \n" +
          "This is where Plex will look for songs from your playlists. \n" +
          "Due to Plex API limitations, all music to be added to playlists must be in the same library.")

    # Display discovered library sections
    plexSections(server_url, plex_token)

    section_id = input("Please enter your music section ID: ")

    br()

    v = {}
    v["server_url"] = server_url
    v["plex_token"] = plex_token
    v["local_playlists"] = local_playlists
    v["v['install_directory']"] = install_directory
    v["section_id"] = section_id
    v["local_prepend"] = local_prepend
    v["plex_prepend"] = plex_prepend
    v["local_convert"] = local_convert
    v["plex_convert"] = plex_convert

    try:
        with open('variables.json', 'w') as f:
            json.dump(v, f)
    except Exception:
        print(Exception)
        raise SystemExit

    print('Setup complete! Variables are saved in variables.json')
    print('If you need to change anything manually you can do so\n'
          'by editing that file')

    br()

    return v


def getArguments():
    desc = "PPP " + vers + ".\n Syncs playlists between Plex and a local directory \n \
    containing .m3u playlist files."

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-setup', action='store_true',
                        help='Force-run the setup procedure')

    parser.add_argument('-nobackups', action='store_true',
                        help='Disable backup of local playlists completely!')

    parser.add_argument('-retention', metavar='n', type=int, nargs=1, default=10,
                        help='Number of previous local playlist backups to keep (Default 10)')

    return parser.parse_args()


# --- MAIN ---

# Get any arguments passed to PPP
args = getArguments()

print("""
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#                     _____  _____  _____                         #
#                    |  __ \\|  __ \\|  __ \\                        #
#                    | |__) | |__) | |__) |                       #
#                    |  ___/|  ___/|  ___/                        #
#                    | |    | |    | |                            #
#                    |_|    |_|    |_|  """ + vers + """                    #
#                                                                 #
#              --- PPP Copyright (C) 2019 XDGFX ---               #
#                                                                 #
#  This program comes with ABSOLUTELY NO WARRANTY.                #
#  This is free software, and you are welcome to redistribute it  #
#  under certain conditions                                       #
#                                                                 #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
\n""")

runtime = str(datetime.now().replace(microsecond=0)
              ).replace(' ', '-').replace(':', '-')
print('Running PPP at ' + runtime + '\n')

if not args.setup:
    print("Attempting to load existing variables...\n")

    try:
        f = open('variables.json')
        v = json.load(f)
        print("Variables loaded successfully!")
    except Exception as e:
        print("INFO: Couldn't find existing variables... proceeding with initial setup\n")
        v = setupVariables()
else:
    print("Forcing setup sequence...")
    v = setupVariables()

br()

print("I'll ignore " + v['local_prepend'] + " from local playlists and " +
      v['plex_prepend'] + " from Plex playlists\n")

# Check if Plex playlists need to be converted
if v['plex_convert'] == "w2l":
    print("Plex playlists will be converted from Windows to Unix directories")
elif v['plex_convert'] == "l2w":
    print("Plex playlists will be converted from Unix to Windows directories")
else:
    print("Plex playlist paths will not be converted")

# Check if local playlists need to be converted
if v['local_convert'] == "w2l":
    print("Local playlists will be converted from Windows to Unix directories")
elif v['local_convert'] == "l2w":
    print("Local playlists will be converted from Unix to Windows directories")
else:
    print("Local playlist paths will not be converted")

br()

# Remove existing temporary directory
if os.path.isdir('.tmp'):
    try:
        shutil.rmtree('.tmp')
    except Exception as e:
        print("ERROR: I couldn't remove existing .tmp folder. Try deleting manually?")
        print(e)
        raise SystemExit

# Create backups folder if required
if not os.path.isdir('local_backups') and not args.nobackups:
    print('No local backups detected... making local_backups folder.')
    os.makedirs('local_backups')

# Folder operations
try:
    print('Attempting to make .tmp folders')
    os.makedirs('.tmp')
    os.makedirs(os.path.join('.tmp', 'plex'))
    os.makedirs(os.path.join('.tmp', 'local'))
    os.makedirs(os.path.join('.tmp', 'merged'))

except Exception as e:
    print('OH NO: Couldn\'t make tmp directories... check your permissions or make sure you don\'t have them open elsewhere')
    print("ERROR: %s", e)
    raise SystemExit

if not args.nobackups:
    backups = os.listdir('local_backups')

    if len(backups) > args.retention:
        oldest_backup = 

    i = 1
    while os.path.exists('local_backups/%s' % i):
        i += 1
    if i > 10:
        size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames,
                    filenames in os.walk('local_backups') for filename in filenames) / 1024 / 1024
        print('You have 10+ backups in your install directory, taking up %sMB of space... You might want to remove some old ones.\n' % round(size, 2))
        print(
            "Alternatively, create an empty file 'NOBACKUPS' in your PPP/ directory")

    # Backup local playlists
    try:
        print('Backing up local playlists...\n')
        shutil.copytree(v['local_playlists'], 'local_backups/%s' % i)
        print(('Backed up local playlists to local_backups/%s/\n' % i))
    except shutil.Error as e:
        print(('Directory not copied. Error: %s' % e))
    except OSError as e:
        print(('Directory not copied. Error: %s' % e))
else:
    print('Not backing up local playlists. If this was NOT intentional, exit the program immediately\n')

# Get list of playlist IDs
url = 'http://' + str(v['server_url']) + \
    '/playlists/?X-Plex-Token=' + str(v['plex_token'])
print(('Getting playlists from ' + str(url) + '\n'))

dom = minidom.parse(urlopen(url))  # Parse the data

# Extract key from each Playlist item as long as it's not a smart playlist
key = dom.getElementsByTagName('Playlist')
key = [items.attributes['key'].value for items in key if items.attributes['smart'].value == "0"]

# Copies Plex playlists to tmp/plex/ folder
for item in key:
    url = 'http://' + str(v['server_url']) + str(item) + \
        '?X-Plex-Token=' + str(v['plex_token'])
    print(('Accessing ' + str(url)))

    dom = minidom.parse(urlopen(url))  # Parse the data (for each playlist)

    # Get title of playlist
    title = dom.getElementsByTagName('MediaContainer')
    # Extract playlist title
    title = [items.attributes['title'].value for items in title]

    print(('Saving Plex playlist: ' + str(title[0]) + '\n'))

    # Get each track and save to file
    file = io.open('tmp/plex/' + str(title[0]) + '.m3u', 'w+', encoding='utf8')

    path = dom.getElementsByTagName('Part')
    # Extract disk path to music file
    path = [items.attributes['file'].value for items in path]

    # Writes music path to .m3u file, repeating for each track
    for i in range(len(path)):
        file.write(path[i] + '\n')
    file.close()

# Copies local playlists to tmp/local/ folder
for root, dirs, files in os.walk(v['local_playlists']):
    for file in files:
        file_path = os.path.join(root, file)

        if file.endswith('.m3u'):
            print(('Copying local playlist: ' + file_path))
            shutil.copy2(file_path, 'tmp/local/')

# Checks for unique playlists to tmp/plex/, and copies them to tmp/merged/
for filename in os.listdir('tmp/plex/'):
    if not os.path.isfile(os.path.join('tmp/local/', filename)):
        print(('Found new Plex playlist: ' + filename))
        plex_tracks = io.open(os.path.join(
            'tmp/plex/', filename), 'r', encoding='utf8').read().splitlines()
        os.remove(os.path.join('tmp/plex/', filename))
        file = io.open('tmp/merged/' + filename, 'w+', encoding='utf8')
        for i in range(len(plex_tracks)):
            plex_tracks[i] = plex_tracks[i].strip(
                v['plex_prepend'])  # Strips v['plex_prepend']
            file.write(plex_tracks[i] + '\n')

# Checks for unique playlists to tmp/local/, and copies them to tmp/merged/
for filename in os.listdir('tmp/local/'):
    if not os.path.isfile(os.path.join('tmp/plex/', filename)):
        print(('Found new local playlist: ' + filename))
        local_tracks = io.open(os.path.join(
            'tmp/local/', filename), 'r', encoding='utf8').read().splitlines()
        os.remove(os.path.join('tmp/local/', filename))
        file = io.open('tmp/merged/' + filename, 'w+', encoding='utf8')
        for i in range(len(local_tracks)):
            # Skips m3u tags beginning with #
            if not local_tracks[i].startswith('#'):
                local_tracks[i] = local_tracks[i].strip(
                    v['local_prepend'])  # Strips v['local_prepend']
                file.write(local_tracks[i] + '\n')
        file.close()

# Merges playlists from tmp/local/ and tmp/plex/ and puts the output in tmp/merged
for filename in os.listdir('tmp/local/'):

    print(('Merging: ' + filename))

    local_tracks = io.open(os.path.join(
        'tmp/local/', filename), 'r', encoding='utf8').read().splitlines()

    for i in range(len(local_tracks)):  # Strips v['local_prepend']
        local_tracks[i] = local_tracks[i].strip(v['local_prepend'])

    plex_tracks = io.open(os.path.join('tmp/plex/', filename),
                          'r', encoding='utf8').read().splitlines()

    for i in range(len(plex_tracks)):  # Strips v['plex_prepend']
        plex_tracks[i] = plex_tracks[i].strip(v['plex_prepend'])

    file = io.open(os.path.join('tmp/merged/', filename),
                   'w+', encoding='utf8')

    for line in local_tracks:  # Writes local_tracks to merged playlist

        if not line.startswith('#'):  # Skips m3u tags beginning with #
            file.write(line + '\n')

        if line in plex_tracks:  # Remove duplicates
            plex_tracks.remove(line)

    for line in plex_tracks:  # Writes plex_tracks to merged playlist
        file.write(line + '\n')

    file.close()

# Copy merged playlists back into tmp/plex/ and tmp/local/ with prepends re-added
for filename in os.listdir('tmp/merged/'):
    new_tracks = io.open(os.path.join('tmp/merged/', filename),
                         'r+', encoding='utf8').read().splitlines()
    plex_tracks = []
    local_tracks = []

    for i in range(len(new_tracks)):  # Re-adds prepends and writes to files
        plex_tracks.append(v['plex_prepend'] + new_tracks[i])
        local_tracks.append(v['local_prepend'] + new_tracks[i])

    file = io.open(os.path.join('tmp/local/', filename), 'w+', encoding='utf8')

    for line in local_tracks:  # Writes local_tracks to merged playlist
        file.write(line + '\n')

    file.close()

    file = io.open(os.path.join('tmp/plex/', filename), 'w+', encoding='utf8')

    for line in plex_tracks:  # Writes local_tracks to merged playlist
        file.write(line + '\n')

    file.close()

# POST new playlists to Plex
url = 'http://' + v['server_url'] + '/playlists/upload?'
headers = {'cache-control': "no-cache"}

for filename in os.listdir('tmp/plex/'):
    print('Sending updated playlist to Plex: ' + filename)

    current_playlist = v['install_directory'] + '\\tmp\\plex\\' + filename

    querystring = urllib.parse.urlencode(OrderedDict(
        [("section_id", v['section_id']), ("path", current_playlist), ("X-Plex-Token", v['plex_token'])]))
    response = requests.post(url, data="", headers=headers, params=querystring)
    # Should return nothing but if there's an issue there may be an error shown
    print(response.text)

# Copy updated local playlists back to v['local_playlists']
for root, dirs, files in os.walk(v['local_playlists']):
    for file in files:
        if file.endswith('.m3u'):
            print('Copying updated playlist to local playlists: ' + file)
            file_path = os.path.join(root, file)
            if os.path.isfile('tmp/local/' + file):
                shutil.copy2('tmp/local/' + file, file_path)
                os.remove('tmp/local/' + file)
            else:
                print(
                    "FAIL: A playlist from v['local_playlists'] was there earlier and now it isn\'t. I am very confused.")
                raise SystemExit

for filename in os.listdir('tmp/local/'):
    shutil.copy2('tmp/local/' + filename, v['local_playlists'])

try:
    shutil.rmtree('tmp/')
    print('Complete!\n')
except shutil.Error as e:
    print('Program complete, but I had trouble cleaning tmp/ directory. Check it\'s not open somewhere else \n Error: %s' % e)
    raise SystemExit
