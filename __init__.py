# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

bl_info = {
    "name": "Blender ID authentication",
    "author": "Francesco Siddi and Inês Almeida",
    "version": (0, 0, 2),
    "blender": (2, 73, 0),
    "location": "Add-on preferences",
    "description":
        "Stores your Blender ID credentials for usage with other add-ons",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User"
}


import bpy
import os
import json
import requests
import socket
from bpy.props import StringProperty
from bpy.types import AddonPreferences
from bpy.types import Operator


class SystemUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    @staticmethod
    def blender_id_endpoint():
        """Gets the endpoint for the authentication API. If the env variable
        is defined, it's possible to override the (default) production address.
        """
        return os.environ.get(
            'BLENDER_ID_ENDPOINT',
            'https://www.blender.org/id'
        )


class ProfilesUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    profiles_path = os.path.join(os.path.expanduser('~'), '.blender_id')
    profiles_file = os.path.join(profiles_path, 'profiles.json')

    @classmethod
    def get_profiles_data(cls):
        """Returns the profiles.json content from a .blender_id folder in the
        user home directory. If the file does not exist we create one with the
        basic data structure.
        """
        profiles_default_data = {
            'active_profile': None,
            'profiles': {}
        }

        # if the file does not exist
        if not os.path.exists(cls.profiles_file):
            try:
                os.makedirs(cls.profiles_path)
            except FileExistsError:
                # the directory is already there, it is just missing the file
                # or the file has no permissions <- TODO
                pass
            except Exception as e:
                raise e

            # populate the file
            with open(cls.profiles_file, 'w') as outfile:
                json.dump(profiles_default_data, outfile)
            return profiles_default_data

        # try parsing the file
        else:
            with open(cls.profiles_file, 'r') as f:
                try:
                    file_data = json.load(f)
                    file_data['active_profile']
                    file_data['profiles']
                    return file_data
                except (
                    KeyError, # it doesn't have the expected content
                    ValueError):
                    #json.decoder.JSONDecodeError):  # empty or malformed json data
                    print("(%s) "
                        "Warning: profiles.json is either empty or malformed. "
                        "The file will be reset." % __name__)

                    # overwrite the file
                    with open(cls.profiles_file, 'w') as outfile:
                        json.dump(profiles_default_data, outfile)
                    return profiles_default_data
                except Exception as e:
                    raise e

    @staticmethod
    def authenticate(username, password):
        """Authenticate the user with a single transaction containing username
        and password (must happen via HTTPS). If the transaction is successful,
        we return the token (that will be used to represent that username and
        password combination) and a message confirming the successful login.
        """
        payload = dict(
            username=username,
            password=password,
            hostname=socket.gethostname())

        try:
            r = requests.post("{0}/u/identify".format(
                SystemUtility.blender_id_endpoint()), data=payload, verify=True)
        except requests.exceptions.SSLError as e:
            print(repr(e))
            raise e
        except requests.exceptions.HTTPError as e:
            print(e)
            raise e
        except requests.exceptions.ConnectionError as e:
            print(e)
            raise e

        if r.status_code == 200:
            r = r.json()
            token = r['data']['token']
            status = r['status']
        else:
            token = None
            status = None
        return dict(
            status=status,
            token=token,
            username=username)

    @classmethod
    def credentials_save(cls, credentials):
        """Given login credentials (Blender-ID username and password), we use
        the authenticate function to generate the token, which we store in the
        profiles.json. Currently we overwrite all credentials with the new one
        if successful.
        """
        authentication = cls.authenticate(
            credentials['username'], credentials['password'])

        if authentication['status'] == 'success':
            profiles = cls.get_profiles_data()['profiles']
            profiles[authentication['username']] = dict(
                username=credentials['username'],
                token=authentication['token'])
            with open(cls.profiles_file, 'w') as outfile:
                json.dump({
                    'active_profile': authentication['username'],
                    'profiles': profiles
                }, outfile)
        return dict(
            status=authentication['status'],
            username=authentication['username'])

    @classmethod
    def credentials_load(cls):
        """Loads all profiles' credentials."""
        return cls.get_profiles_data()['profiles']

    @classmethod
    def credentials_load(cls, username):
        """Loads the credentials from a profile file given a username."""
        if username == '':
            return None

        profile = cls.get_profiles_data()['profiles'][username]
        return dict(
            username=profile['username'],
            token=profile['token'])

    @classmethod
    def get_active_username(cls):
        """Get the currently active username. If there is no
        active profile on the file, this function will return None.
        """
        cls.get_profiles_data()['active_profile']

    @classmethod
    def get_active_profile(cls):
        """Pick the active profile from the profiles.json. If there is no
        active profile on the file, this function will return None.
        """
        username = cls.get_active_username()
        if username == None:
            return None
        else:
            return cls.credentials_load(username)

    @classmethod
    def logout(cls, username):
        """Invalidates the token and state of active for this username.
        This is different from switching the active profile, where the active
        profile is changed but there isn't an explicit logout.
        """
        file_content = cls.get_profiles_data()
        # Remove user from 'active profile'
        if file_content['active_profile'] == username:
            file_content['active_profile'] = None
        # Remove both user and token from profiles list
        if username in file_content['profiles']:
            del file_content['profiles'][username]
        with open(cls.profiles_file, 'w') as outfile:
            json.dump(file_content, outfile)

        # TODO: invalidate login token for this user on the server


class BlenderIdPreferences(AddonPreferences):
    bl_idname = __name__

    profile = ProfilesUtility.get_active_profile()
    if profile:
        username = profile['username']
    else:
        username = ''

    blender_id_username = StringProperty(
        name='Username',
        default=username,
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    blender_id_password = StringProperty(
        name='Password',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD'
    )

    def draw(self, context):
        layout = self.layout
        if self.username != '':
            text = "You are logged in as {0}".format(self.username)
            layout.label(text=text, icon='WORLD_DATA')
            layout.operator('blender_id.logout')
        else:
            layout.prop(self, 'blender_id_username')
            layout.prop(self, 'blender_id_password')
            layout.operator('blender_id.save_credentials')


class BlenderIdSaveCredentials(Operator):
    bl_idname = 'blender_id.save_credentials'
    bl_label = 'Save credentials'

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences
        credentials = dict(
            username=addon_prefs.blender_id_username,
            password=addon_prefs.blender_id_password)
        try:
            r = ProfilesUtility.credentials_save(credentials)
        except Exception as e:
            self.report({'ERROR'}, "Can't connect to {0}".format(
                SystemUtility.blender_id_endpoint()))

        return{'FINISHED'}


class BlenderIdLogout(Operator):
    bl_idname = 'blender_id.logout'
    bl_label = 'Logout'

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences
        try:
            r = ProfilesUtility.logout(addon_prefs.blender_id_username)
        except Exception as e:
            self.report(e)

        return{'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == '__main__':
    register()
