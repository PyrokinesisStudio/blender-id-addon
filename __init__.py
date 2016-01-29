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
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/System/BlenderID",
    "category": "System",
    "support": "TESTING"
}


import bpy
import os
import json
import requests
import socket
from bpy.types import AddonPreferences
from bpy.types import Operator
from bpy.types import PropertyGroup
from bpy.props import IntProperty
from bpy.props import StringProperty
from bpy.props import PointerProperty


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
        ).rstrip('/')


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
        and password (must happen via HTTPS).
        If the transaction is successful, status will be 'successful' and we
        return the user's unique blender id and a token (that will be used to
        represent that username and password combination).
        If there was a problem, status will be 'fail' and we return an error
        message. Problems may be with the connection or wrong user/password.
        """
        payload = dict(
            username=username,
            password=password,
            hostname=socket.gethostname()
        )
        try:
            r = requests.post("{0}/u/identify".format(
                SystemUtility.blender_id_endpoint()), data=payload, verify=True)
        except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
            r = lambda: None # just create an empty object
            r.status_code = type(e).__name__

        user_id = None
        token = None
        error_message = None

        if r.status_code == 200:
            resp = r.json()
            status = resp['status']
            if status == 'success':
                user_id = resp['data']['user_id']
                token = resp['data']['token']
            elif status == 'fail':
                if 'username' in resp['data']:
                    error_message = "Username does not exist"
                elif 'password' in resp['data']:
                    error_message = "Password does not match!"
        else:
            status = 'fail'
            error_message = format("There was a problem communicating with"
                " the server. Error code is: %s" % r.status_code)

        return dict(
            status=status,
            user_id=user_id,
            token=token,
            error_message=error_message
        )

    @classmethod
    def save_active_profile(cls, user_id, token, username):
        """Saves a new profile and marks it as the active one
        """
        profiles = cls.get_profiles_data()['profiles']
        # overwrite or create new profile entry for this user_id
        profiles[user_id] = dict(
            username=username,
            token=token
        )
        with open(cls.profiles_file, 'w') as outfile:
            json.dump({
                'active_profile': user_id,
                'profiles': profiles
            }, outfile)

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
    def logout(cls, user_id):
        """Invalidates the token and state of active for this user.
        This is different from switching the active profile, where the active
        profile is changed but there isn't an explicit logout.
        """
        file_content = cls.get_profiles_data()
        # Remove user from 'active profile'
        if file_content['active_profile'] == user_id:
            file_content['active_profile'] = 0
        # Remove both user and token from profiles list
        if user_id in file_content['profiles']:
            del file_content['profiles'][user_id]
        with open(cls.profiles_file, 'w') as outfile:
            json.dump(file_content, outfile)

        # TODO: invalidate login token for this user on the server


class BlenderIdPreferences(AddonPreferences):
    bl_idname = __name__

    p_username = ''
    profile = ProfilesUtility.get_active_profile()
    if profile:
        p_username = profile['username']

    error_message = StringProperty(
        name='Error Message',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    blender_id_username = StringProperty(
        name='Username',
        default=p_username,
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
        active_profile = context.window_manager.blender_id_active_profile
        if active_profile.unique_id > 0:
            text = "You are logged in as {0}".format(active_profile.unique_id)
            layout.label(text=text, icon='WORLD_DATA')
            layout.operator('blender_id.logout')
        else:
            if self.error_message:
                layout.label(self.error_message)
            layout.prop(self, 'blender_id_username')
            layout.prop(self, 'blender_id_password')
            layout.operator('blender_id.login')


class BlenderIdLogin(Operator):
    bl_idname = 'blender_id.login'
    bl_label = 'Login'

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__name__].preferences
        active_profile = context.window_manager.blender_id_active_profile

        resp = ProfilesUtility.authenticate(
            username=addon_prefs.blender_id_username,
            password=addon_prefs.blender_id_password
        )

        if resp['status'] == "success":
            active_profile.unique_id = resp['user_id']
            active_profile.token = resp['token']

            ProfilesUtility.save_active_profile(
                resp['user_id'],
                resp['token'],
                addon_prefs.blender_id_username
            )
        else:
            addon_prefs.error_message = resp['error_message']
        return{'FINISHED'}


class BlenderIdLogout(Operator):
    bl_idname = 'blender_id.logout'
    bl_label = 'Logout'

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__name__].preferences
        active_profile = context.window_manager.blender_id_active_profile

        r = ProfilesUtility.logout(active_profile.unique_id)
        active_profile.unique_id = 0
        active_profile.token = ""
        addon_prefs.error_message = ""
        return{'FINISHED'}


class BlenderIdProfile(PropertyGroup):

    unique_id = IntProperty(
        name='ID',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    token = StringProperty(
        name='Token',
        options={'HIDDEN', 'SKIP_SAVE'}
    )


def register():
    bpy.utils.register_module(__name__)

    bpy.types.WindowManager.blender_id_active_profile = \
        PointerProperty(type=BlenderIdProfile, name='Blender ID Active Profile')


def unregister():
    del bpy.types.WindowManager.blender_id_active_profile

    bpy.utils.unregister_module(__name__)


if __name__ == '__main__':
    register()
