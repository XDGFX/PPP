# --- PPP (Plex Playlist Pusher) v3.0.0 ---
# Synchronises playlists between local files (.m3u) and Plex playlists.
# If there are differences between local and Plex playlists, both will be
# merged and duplicates deleted; meaning tracks can be added on one and
# updated on both... but must be deleted on BOTH to remove completely
# (the same goes for new playlists).

# XDGFX 2019

# 17/03/19 Started working on script
# 19/03/19 Original v2.0 Release (where v1.0 was bash version)
# 20/03/19 v2.1 Updated to use tempfile module temporary directory
# 22/03/19 v2.1.1 General improvements and bug fixes
# 23/03/19 v2.1.2 Fixed v2.1 and v2.1.1 releases, no longer using tempfile
# 30/03/19 v2.1.3 Added timestamp and improved character support
# 20/12/19 v3.0.0 MAJOR REWRITE: Added setup procedure and UNIX / Windows compatibility

# Uses GNU General Public License


# --- IMPORT MODULES ---

from datetime import datetime                # for timestamp
import requests                              # HTTP POST requests
from collections import OrderedDict          # url ordering
import io                                    # character encoding
import os                                    # for folder and file management
import shutil                                # for deleting files
import argparse                              # for arguments
from xml.etree import ElementTree            # for xml
import urllib                                # for Plex POST
import re                                    # for verifying input variables
import json                                  # for saving of variables
import warnings                              # for hiding SSL warnings when cert checking is disabled


# --- FUNCTIONS ---

def br():
    print("\n------\n")


def plexSections(server_url, plex_token, check_ssl):
    try:
        print("Requesting section info from Plex...")
        url = server_url + "/library/sections/all?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30, verify=check_ssl)

        if resp.status_code == 200:
            print("Requesting of section info was successful.")

            br()

            root = ElementTree.fromstring(resp.text)
            print("ID: SECTION")

            for document in root.findall("Directory"):
                if document.get('type') == "artist":
                    print(document.get('key') + ': ' +
                          document.get('title').strip())

    except Exception:
        print("ERROR: Issue encountered when attempting to list detailed sections info.")
        raise SystemExit


def plexPlaylistKeys(server_url, plex_token, check_ssl):
    try:
        print("Requesting playlists from Plex...")
        url = server_url + "/playlists/?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30, verify=check_ssl)

        if resp.status_code == 200:
            print("Requesting of playlists was successful.")
            root = ElementTree.fromstring(resp.text)

            keys = []
            for document in root.findall("Playlist"):
                if document.get('smart') == "0" and document.get('playlistType') == "audio":
                    keys.append(document.get('key'))

            print("Found " + str(len(keys)) + " playlists.")

            br()

            return keys

    except Exception as e:
        print("ERROR: Issue encountered when attempting to list detailed sections info.")
        print('ERROR: %s' % e)
        raise SystemExit


def plexPlaylist(server_url, plex_token, key, check_ssl):
    try:
        print("Requesting playlist data from Plex...")
        url = server_url + key + "?X-Plex-Token=" + plex_token
        print("URL: " + url.replace(plex_token, "***********"))
        resp = requests.get(url, timeout=30, verify=check_ssl)

        if resp.status_code == 200:
            root = ElementTree.fromstring(resp.text)

            title = root.get("title")

            print("Found playlist: " + title)

            playlist = []
            for document in root.findall("Track"):
                playlist.append(document[0][0].get('file'))

            print("Found " + str(len(playlist)) + " songs.")

            return title, playlist

    except Exception as e:
        print("ERROR: Issue encountered when attempting to get Plex playlist.")
        print('ERROR: %s' % e)
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
          "check variables.json is present, and accessible by PPP.")

    br()

    # UNIX CHECK
    ppp_unix = True if not os.name == "nt" else False
    plex_convert = False
    local_convert = False

    print("It looks like your PPP machine uses %s paths" %
          ("UNIX" if ppp_unix else "Windows"))

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
        input("WARNING: Entered token '" + plex_token + "' does not appear to follow the correct format!\n" +
              "If you believe this is a mistake, press enter to continue... ")

        br()
    
    # Decide if SSL cert should be enforced
    print("Would you like to check SSL certificates? If unsure press enter for default")
    check_ssl = input("Validate SSL certificate? - enabled by default (y / n): ")
    
    if (check_ssl == "n" or check_ssl == "N"):
        check_ssl = False
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    else:
        check_ssl = True

    br()
    
    # Fetch Plex music playlist keys
    keys = plexPlaylistKeys(server_url, plex_token, check_ssl)

    br()

    print("Fetching sample playlist to determine prepend...")
    _, playlist = plexPlaylist(server_url, plex_token, keys[0], check_ssl)

    plex_unix = playlist[0].startswith("/")

    print("It looks like your Plex machine uses %s paths" %
          ("UNIX" if plex_unix else "Windows"))

    # Convert from Windows to UNIX paths
    if plex_unix != ppp_unix:

        print("Plex playlists are not in PPP directory format!")
        print("Attempting to convert Plex directories to PPP machine format")

        if ppp_unix:
            plex_convert = "w2u"
        else:
            plex_convert = "u2w"

    playlist = [convertPath(track, plex_convert, False) for track in playlist]

    plex_prepend = os.path.commonpath(playlist)

    # Convert paths back for prepend
    playlist = [convertPath(track, plex_convert, True) for track in playlist]

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

    print("It looks like your local playlists use %s paths" %
          ("UNIX" if local_unix else "Windows"))

    # Convert paths
    if local_unix != ppp_unix:

        print("Local playlists are not in PPP directory format!")
        print("Attempting to convert local directories to PPP machine format")

        if ppp_unix:
            local_convert = 'w2u'
        else:
            local_convert = 'u2w'

    playlist = [convertPath(track, local_convert, False) for track in playlist]

    local_prepend = os.path.commonpath(playlist)

    # Convert paths back for prepend
    playlist = [convertPath(track, local_convert, True) for track in playlist]

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
    plexSections(server_url, plex_token, check_ssl)

    section_id = input("Please enter your music section ID: ")

    br()

    v = {}
    v["server_url"] = server_url
    if (check_ssl == False):
        v["check_ssl"] = "False"
    else:
        v["check_ssl"] = "True"
    v["plex_token"] = plex_token
    v["local_playlists"] = local_playlists
    v["install_directory"] = install_directory
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


def backupLocal():
    if not args.nobackups:
        backups = os.listdir('local_backups')
        backup_time = [b.replace('-', '') for b in backups]

        while len(backups) > args.retention:
            print('INFO: Number of backups (%i) exceeds backup retention (%i)' %
                  (len(backups), args.retention))
            oldest_backup = backup_time.index(min(backup_time))

            # Delete oldest backup
            shutil.rmtree(os.path.join(
                'local_backups', backups[oldest_backup]))
            del backups[oldest_backup], backup_time[oldest_backup]

            print('Deleted oldest backup')
            br()

        # Backup local playlists
        try:
            print('Backing up local playlists...\n')
            shutil.copytree(v['local_playlists'],
                            os.path.join('local_backups', runtime))
            print('Backed up local playlists to ' +
                  os.path.join('local_backups', runtime))
        except Exception:
            print('Directory not copied.')
            print('ERROR: %s' % Exception)
            raise SystemExit

        # Calculate backup size
        size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames,
                   filenames in os.walk('local_backups') for filename in filenames) / 1024 / 1024
        print('INFO: Your backups are currently taking up %sMB of space' %
              round(size, 2))

    else:
        print('Not backing up local playlists. If this was NOT intentional, exit the program immediately\n')

    br()


def setupFolders():

    # Remove existing temporary directory
    if os.path.isdir('.tmp'):
        try:
            shutil.rmtree('.tmp')
        except Exception as e:
            print("ERROR: I couldn't remove existing .tmp folder. Try deleting manually?")
            print(e)
            raise SystemExit

    # Folder operations
    try:
        print('Attempting to make .tmp folders')
        os.makedirs('.tmp')
        os.makedirs(_plex)
        os.makedirs(_local)
        os.makedirs(_merged)
        print('Successfully created .tmp folders')

    except Exception as e:
        print('OH NO: Couldn\'t make tmp directories... check your permissions or make sure you don\'t have them open elsewhere')
        print('ERROR: %s' % e)
        raise SystemExit

    # Create backups folder if required
    if not os.path.isdir('local_backups') and not args.nobackups:
        print('No local backups detected... making local_backups folder.')
        os.makedirs('local_backups')

    br()


def convertPath(path, convert, invert):
    if convert == False:
        return path
    elif convert == ('w2u' and not invert) or ('u2w' and invert):
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")


def stripPrepend(path, prepend, invert):
    if not invert:
        return path.replace(prepend, '')
    else:
        return prepend + path


# --- MAIN ---

# Setup version and get any arguments passed to PPP
vers = "v3.0.0"
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
if v['plex_convert'] == "w2u":
    print("Plex playlists will be converted from Windows to Unix directories")
elif v['plex_convert'] == "u2w":
    print("Plex playlists will be converted from Unix to Windows directories")
else:
    print("Plex playlist paths will not be converted")

# Check if local playlists need to be converted
if v['local_convert'] == "w2u":
    print("Local playlists will be converted from Windows to Unix directories")
elif v['local_convert'] == "u2w":
    print("Local playlists will be converted from Unix to Windows directories")
else:
    print("Local playlist paths will not be converted")

if v['check_ssl'] == "False":
    print("SSL certificate will not be validated")
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    check_ssl=False
else:
    print("SSL certificate will be validated")
    check_ssl=True
br()

# Create tmp and backup folders if required
_local = os.path.join('.tmp', 'local')
_plex = os.path.join('.tmp', 'plex')
_merged = os.path.join('.tmp', 'merged')

setupFolders()

# Run backups of local playlists
backupLocal()

# Get keys for all Plex music playlists
keys = plexPlaylistKeys(v['server_url'], v['plex_token'], check_ssl)

# Copies Plex playlists to .tmp/plex/ folder
for key in keys:
    title, playlist = plexPlaylist(v['server_url'], v['plex_token'], key, check_ssl)

    # Strip prepend
    playlist = [stripPrepend(track, v['plex_prepend'], False)
                for track in playlist]

    # Convert to PPP path style
    playlist = [convertPath(track, v['plex_convert'], False)
                for track in playlist]

    print('Saving Plex playlist: ' + title)

    # Get each track and save to file
    f = io.open(os.path.join(_plex, title + '.m3u'),
                'w+', encoding='utf8')
    for track in playlist:
        f.write(track + '\n')
    f.close()

    print('Save successful!')

    br()

# Copies local playlists to .tmp/local/ folder
for root, dirs, files in os.walk(v['local_playlists']):
    for file in files:
        file_path = os.path.join(root, file)

        if file.endswith('.m3u'):

            playlist = io.open(
                file_path, 'r', encoding='utf8').read().splitlines()

            # Strip prepend
            playlist = [stripPrepend(track, v['local_prepend'], False)
                        for track in playlist]

            # Convert to PPP path style
            playlist = [convertPath(track, v['local_convert'], False)
                        for track in playlist]

            print(('Copying local playlist: ' + file_path))

            # Get each track and save to file
            f = io.open(os.path.join(_local, file),
                        'w+', encoding='utf8')
            for track in playlist:
                f.write(track + '\n')
            f.close()

br()

# Checks for unique playlists to .tmp/plex/, and moves them to .tmp/merged/
for filename in os.listdir(_plex):
    if not os.path.isfile(os.path.join(_local, filename)):
        print(('Found new Plex playlist: ' + filename))

        os.rename(os.path.join(_plex, filename),
                  os.path.join(_merged, filename))

        br()

# Checks for unique playlists to .tmp/local/, and copies them to .tmp/merged/
for filename in os.listdir(_local):
    if not os.path.isfile(os.path.join(_plex, filename)):
        print(('Found new local playlist: ' + filename))

        os.rename(os.path.join(_local, filename),
                  os.path.join(_merged, filename))

        br()

# Merges playlists from tmp/local/ and tmp/plex/ and puts the output in tmp/merged
for filename in os.listdir(_local):

    print(('Merging: ' + filename))

    local_tracks = io.open(os.path.join(
        _local, filename), 'r', encoding='utf8').read().splitlines()

    plex_tracks = io.open(os.path.join(
        _plex, filename), 'r', encoding='utf8').read().splitlines()

    f = io.open(os.path.join(_merged, filename), 'w+', encoding='utf8')

    for line in local_tracks:  # Writes local_tracks to merged playlist
        if not line.startswith('#'):  # Skips m3u tags beginning with #
            f.write(line + '\n')
        if line in plex_tracks:  # Remove duplicates
            plex_tracks.remove(line)

    for line in plex_tracks:  # Writes plex_tracks to merged playlist
        f.write(line + '\n')
    f.close()

br()

# Copy merged playlists back into tmp/plex/ and tmp/local/ with prepends re-added
for filename in os.listdir(_merged):
    new_tracks = io.open(os.path.join(_merged, filename),
                         'r+', encoding='utf8').read().splitlines()
    plex_tracks = []
    local_tracks = []

    for track in new_tracks:  # Re-adds prepends and writes to files
        plex_tracks.append(stripPrepend(convertPath(
            track, v['plex_convert'], True), v['plex_prepend'], True))

        local_tracks.append(stripPrepend(convertPath(
            track, v['local_convert'], True), v['local_prepend'], True))

    # Writes local_tracks to merged playlist
    f = io.open(os.path.join(_local, filename), 'w+', encoding='utf8')
    for line in local_tracks:
        f.write(line + '\n')
    f.close()

    # Writes local_tracks to merged playlist
    f = io.open(os.path.join(_plex, filename), 'w+', encoding='utf8')
    for line in plex_tracks:
        f.write(line + '\n')
    f.close()

# POST new playlists to Plex
url = v['server_url'] + '/playlists/upload?'
headers = {'cache-control': "no-cache"}

for filename in os.listdir(_plex):
    print('Sending updated playlist to Plex: ' + filename)

    _plex_path = convertPath(os.path.join(
        v['install_directory'], _plex, filename), v['plex_convert'], True)

    querystring = urllib.parse.urlencode(OrderedDict(
        [("sectionID", v['section_id']), ("path", _plex_path), ("X-Plex-Token", v['plex_token'])]))
    response = requests.post(url, data="", headers=headers, params=querystring, verify=check_ssl)

    # Should return nothing but if there's an issue there may be an error shown
    print(response.text)

br()

# Copy updated local playlists back to v['local_playlists']
for root, _, files in os.walk(v['local_playlists']):
    for playlist in files:
        if playlist.endswith('.m3u'):
            print('Copying updated playlist to local playlists: ' + playlist)
            target_path = os.path.join(root, playlist)
            local_path = os.path.join(_local, playlist)

            if os.path.isfile(local_path):
                shutil.copy2(local_path, target_path)
                os.remove(local_path)
            else:
                print(
                    "FAIL: A playlist from v['local_playlists'] was there earlier and now it isn\'t. I am very confused.")
                raise SystemExit

# Copy remaining, new playlists to the root directory
for playlist in os.listdir(_local):
    shutil.copy2(os.path.join(_local, playlist), v['local_playlists'])

br()

try:
    shutil.rmtree('.tmp')
    print('Complete!\n')
except shutil.Error as e:
    print("Program complete, but I had trouble cleaning .tmp directory. Check it's not open somewhere else \n ERROR: %s" % e)
    raise SystemExit
