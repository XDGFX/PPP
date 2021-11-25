#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
--- PPP (Plex Playlist Pusher) ---
Synchronises playlists between local files (.m3u) and Plex playlists.
If there are differences between local and Plex playlists, both will be
merged and duplicates deleted; meaning tracks can be added on one and
updated on both... but must be deleted on BOTH to remove completely
(the same goes for new playlists).

XDGFX 2020

17/03/19 Started working on script
19/03/19 Original v2.0 Release (where v1.0 was bash version)
20/03/19 v2.1 Updated to use tempfile module temporary directory
22/03/19 v2.1.1 General improvements and bug fixes
23/03/19 v2.1.2 Fixed v2.1 and v2.1.1 releases, no longer using tempfile
30/03/19 v2.1.3 Added timestamp and improved character support
20/12/19 v3.0.0 MAJOR REWRITE: Added setup procedure and UNIX / Windows compatibility
30/12/19 v3.0.1 Added ability to ignore SSL certificates
02/01/20 v3.0.2 Fixed prepend conversion when PPP and playlist machine not same type
07/01/20 v3.0.3 Touches and tweaks by cjnaz
09/01/20 v3.0.4 Fixed custom retention arguments
17/04/20 v3.0.5 Improved support for Plex running in containers by gotson
01/09/20 v3.0.6 General cleanup by pirtoo

Uses GNU General Public License
"""


# --- IMPORT MODULES ---
import warnings
import json                                  # for saving of variables
import re                                    # for verifying input variables
import urllib                                # for Plex POST
from xml.etree import ElementTree            # for xml
import argparse                              # for arguments
import shutil                                # for deleting files
import os                                    # for folder and file management
import io                                    # character encoding
from collections import OrderedDict          # url ordering
import requests                              # HTTP POST requests
from datetime import datetime                # for timestamp

vers = "v3.0.6"


# --- FUNCTIONS ---

def br():
    print("\n------\n")


def plexGetRequest(url, plex_token, check_ssl):
    print("URL: " + url.replace(plex_token, "***********"))
    try:
        resp = requests.get(url, timeout=30, verify=check_ssl)
        if resp.ok:
            print("Request was successful.")
            br()
            return ElementTree.fromstring(resp.text)
    except Exception:
        print("ERROR: Issue encountered with request.")
        raise SystemExit

    print("ERROR: Request failed.")
    print('ERROR: Return code: %d Reason: %s' %
          (resp.status_code, resp.reason))
    raise SystemExit


def plexSections(server_url, plex_token, check_ssl):
    print("Requesting section info from Plex...")
    url = server_url + "/library/sections/all?X-Plex-Token=" + plex_token
    root = plexGetRequest(url, plex_token, check_ssl)
    br()
    print("ID: SECTION")
    for document in root.findall("Directory"):
        if document.get('type') == "artist":
            print(document.get('key') + ': ' +
                  document.get('title').strip())


def plexPlaylistKeys(server_url, plex_token, check_ssl):
    print("Requesting playlists from Plex...")
    url = server_url + "/playlists/?X-Plex-Token=" + plex_token
    root = plexGetRequest(url, plex_token, check_ssl)
    keys = []
    for document in root.findall("Playlist"):
        if document.get('smart') == "0" and document.get('playlistType') == "audio":
            keys.append(document.get('key'))
    print("Found " + str(len(keys)) + " playlists.")
    br()
    return keys


def plexPlaylist(server_url, plex_token, key, check_ssl):
    print("Requesting playlist data from Plex...")
    url = server_url + key + "?X-Plex-Token=" + plex_token
    root = plexGetRequest(url, plex_token, check_ssl)
    title = root.get("title")
    print("Found playlist: " + title)
    playlist = []
    for document in root.findall("Track"):
        playlist.append(document[0][0].get('file'))

    print("Found " + str(len(playlist)) + " songs.")
    return title, playlist


def setupVariables():
    # Remove variables.json if it already exists
    if os.path.isfile('variables.json'):
        try:
            os.remove('variables.json')
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
    server_url = input("Please enter your server URL: ").strip()

    if not re.match('(?:http|https)://', server_url):
        server_url = "http://" + server_url

    br()

    # Regex to check URL with port
    if re.compile(r"^(?:http|https)://[\d.\w]+:[\d]+$").match(server_url) is None:
        input("WARNING: Entered URL '" + server_url + "' does not appear to follow the correct format!\n" +
              "If you believe the entered URL is correct, press enter to continue (else ^C and start over)... ")

        br()

    # PLEX TOKEN
    print("Next we need your Plex Token. You can find this by following these instructions: https://bit.ly/2p7RtOu")
    plex_token = input("Please enter your Plex Token: ").strip()

    br()

    # Regex to check token
    if re.compile(r"^[A-Za-z1-9-_]+$").match(plex_token) is None:
        input("WARNING: Entered token '" + plex_token + "' does not appear to follow the correct format!\n" +
              "If you believe the entered token is correct, press enter to continue (else ^C and start over)... ")

        br()

    # Decide if SSL cert should be enforced
    print("Would you like to check SSL certificates? If unsure press enter for default")
    check_ssl = input(
        "Validate SSL certificate? - enabled by default (y / n): ")

    if (check_ssl == "n" or check_ssl == "N"):
        check_ssl = "False"
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    else:
        check_ssl = "True"

    br()

    # Fetch Plex music playlist keys
    keys = plexPlaylistKeys(server_url, plex_token, check_ssl)

    br()

    if len(keys) == 0:
        print("At least one playlist must exist in Plex in order to determine the Plex machine type.")
        print("Create a dummy playlist in Plex containing at least two titles from different artists, then rerun this script.")
        raise SystemExit

    print("Fetching sample playlist(s) to determine prepend...")
    _, playlist = plexPlaylist(server_url, plex_token, keys[0], check_ssl)
    plex_unix = playlist[0].startswith("/")

    print("It looks like your Plex machine uses %s paths" %
          ("UNIX" if plex_unix else "Windows"))

    # If we have more than one playlist add the second to get better deta for the prefix
    if len(keys) > 1:
        _, playlist_extra = plexPlaylist(
            server_url, plex_token, keys[1], check_ssl)
        playlist = playlist + playlist_extra

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
    plex_prepend = convertPath(plex_prepend, plex_convert, True)

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
    local_prepend = convertPath(local_prepend, local_convert, True)

    print("Calculated local Prepend: " + local_prepend)

    br()

    # WORKING DIRECTORY
    print("Now we need your PPP working directory, relative to PPP.py. \n" +
          "It needs to be accessible by both PPP and Plex. If Plex is running in a container, you can specify another "
          "path afterwards.")
    working_directory = input(
        "Please enter your PPP working directory: ")

    working_directory_plex = input(
        "Please enter your PPP working directory, as seen by Plex (required only if different from previous one): ")
    if working_directory_plex.strip() == '':
        working_directory_plex = working_directory

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
    v["check_ssl"] = check_ssl
    v["plex_token"] = plex_token
    v["local_playlists"] = local_playlists
    v["working_directory"] = working_directory
    v["working_directory_plex"] = working_directory_plex
    v["section_id"] = section_id
    v["local_prepend"] = local_prepend
    v["plex_prepend"] = plex_prepend
    v["local_convert"] = local_convert
    v["plex_convert"] = plex_convert

    try:
        with open('variables.json', 'w') as f:
            json.dump(v, f, indent=2)
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

    parser.add_argument('-retention', metavar='n', type=int, nargs=1, default=[10],
                        help='Number of previous local playlist backups to keep (Default 10)')

    parser.add_argument('-nocleanup', action='store_true',
                        help='Disable removal of .tmp directory (for debug)')

    return parser.parse_args()


def backupLocal():
    if not args.nobackups:
        backups = os.listdir('local_backups')
        backup_time = [b.replace('-', '') for b in backups]

        while len(backups) > args.retention[0]:
            print('INFO: Number of backups (%i) exceeds backup retention (%i)' %
                  (len(backups), args.retention[0]))
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
    if os.path.isdir(_tmp):
        try:
            shutil.rmtree(_tmp)
        except Exception as e:
            print("ERROR: I couldn't remove existing .tmp folder. Try deleting manually?")
            print(e)
            raise SystemExit

    # Folder operations
    try:
        print('Attempting to make .tmp folders')
        os.makedirs(_tmp)
        os.makedirs(_plex)
        os.makedirs(_local)
        os.makedirs(_merged)
        print('Successfully created .tmp folders')

    except Exception as e:
        print("OH NO: Couldn't make tmp directories... check your permissions or make sure you don't have them open elsewhere")
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
    elif (convert == 'w2u' and not invert) or (convert == 'u2w' and invert):
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")


def stripPrepend(path, prepend, invert):
    if not invert:
        return path.replace(prepend, '')
    else:
        return prepend + path


# --- MAIN ---

# Get passed arguments
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
#              --- PPP Copyright (C) 2020 XDGFX ---               #
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

    if os.path.exists('variables.json'):
        if not os.access('variables.json', os.R_OK):
            print("ERROR: Unable to load variables... variables.json file not readable.")
            raise SystemExit
        try:
            f = open('variables.json')
            v = json.load(f)
            print("Variables loaded successfully!")
        except Exception as e:
            print("ERROR: Unable to load variables... check file contains valid json!")
            raise SystemExit
    else:
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
    print("SSL certificates will not be validated")
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    check_ssl = False
else:
    print("SSL certificates will be validated")
    check_ssl = True
br()

# Create tmp and backup folders if required
_tmp = os.path.join(v["working_directory"], '.tmp')
_local = os.path.join(_tmp, 'local')
_plex = os.path.join(_tmp, 'plex')
_merged = os.path.join(_tmp, 'merged')

setupFolders()

# Run backups of local playlists
backupLocal()

# Get keys for all Plex music playlists
keys = plexPlaylistKeys(v['server_url'], v['plex_token'], check_ssl)

# Copies Plex playlists to .tmp/plex/ folder
for key in keys:
    title, playlist = plexPlaylist(
        v['server_url'], v['plex_token'], key, check_ssl)

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

    # Writes local tracks back to local tmp
    f = io.open(os.path.join(_local, filename), 'w+', encoding='utf8')
    for line in local_tracks:
        f.write(line + '\n')
    f.close()

    # Writes plex tracks back to plex tmp
    f = io.open(os.path.join(_plex, filename), 'w+', encoding='utf8')
    for line in plex_tracks:
        f.write(line + '\n')
    f.close()

# POST new playlists to Plex
url = v['server_url'] + '/playlists/upload?'
headers = {'cache-control': "no-cache"}

failed = 0
for filename in os.listdir(_plex):
    print('Sending updated playlist to Plex: ' + filename)

    _plex_path = convertPath(os.path.join(
        v['working_directory_plex'], '.tmp', 'plex', filename), v['plex_convert'], True)

    querystring = urllib.parse.urlencode(OrderedDict(
        [("sectionID", v['section_id']), ("path", _plex_path), ("X-Plex-Token", v['plex_token'])]))
    resp = requests.post(
        url, data="", headers=headers, params=querystring, verify=check_ssl)

    # If the post failed then print the return code and the reason for failing.
    if not resp.ok:
        print('ERROR: Return code: %d Reason: %s' %
              (resp.status_code, resp.reason))
        failed += 1

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
                    "FAIL: A playlist from v['local_playlists'] was there earlier and now it isn't. I am very confused.")
                raise SystemExit

# Copy remaining, new playlists to the root directory
for playlist in os.listdir(_local):
    shutil.copy2(os.path.join(_local, playlist), v['local_playlists'])

br()

if failed:
    print('\nERROR: %d playlists failed to update to plex' % failed)

if not args.nocleanup:
    try:
        shutil.rmtree(_tmp)
        print('Complete!\n')
    except shutil.Error as e:
        print("Program complete, but I had trouble cleaning .tmp directory. Check it's not open somewhere else \n ERROR: %s" % e)
        raise SystemExit
