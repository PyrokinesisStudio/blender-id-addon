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

bl_info = {
    "name": "Blender ID authentication",
    "author": "Francesco Siddi",
    "version": (0, 0, 1),
    "blender": (2, 73, 0),
    "location": "",
    "description": "Stores your Blender ID credentials",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User"}


import bpy
import os

from bpy.props import StringProperty
from bpy.types import AddonPreferences


class SystemUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    @staticmethod 
    def blender_id_endpoint():
        """Gets the endpoint for the authentication API. If the env variable
        is defined, it's possible to override the (default) production address.
        """
        return os.environ.get('BLENDER_ID_ENDPOINT', "http://www.blender.org/id")


class ProfilesUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    @staticmethod 
    def get_profiles_file():
        """Returns the profiles.json filepath from a .blender_id folder in the user
        home directory. If the file does not exist we create one with the basic data
        structure.
        """
        profiles_path = os.path.join(os.path.expanduser('~'), '.blender_id')
        profiles_file = os.path.join(profiles_path, 'profiles.json')
        if not os.path.exists(profiles_file):
            profiles = [{
                "username" : "",
                "token" : "",
                "is_active" : False}]
            try:
                os.makedirs(profiles_path)
            except FileExistsError:
                pass
            except Exception as e:
                raise e

            import json
            with open(profiles_file, 'w') as outfile:
                json.dump(profiles, outfile)
        return profiles_file

    @staticmethod 
    def authenticate(username, password):
        """Authenticate the user with a single transaction containing username and
        password (must happen via HTTPS). If the transaction is successful, we return
        the token (that will be used to represent that username and password combination)
        and a message confirming the succesful login.
        """
        import requests
        import socket
        payload = dict(
            username=username,
            password=password,
            hostname=socket.gethostname())
        try:
            r = requests.post("{0}/u/identify".format(
                SystemUtility.blender_id_endpoint()), data=payload)
        except requests.exceptions.ConnectionError as e:
            raise e

        message = r.json()['message']
        if r.status_code == 200:
            authenticated = True
            token = r.json()['token']
        else:
            authenticated = False
            token = None
        return dict(authenticated=authenticated, message=message, token=token)

    @classmethod
    def credentials_load(cls):
        """Loads the credentials from a profile file. TODO: add a username arg
        so that one out of many identities can be retrieved.
        """
        import json
        profiles_file = cls.get_profiles_file()
        with open(profiles_file) as f:
            return json.load(f)

    @classmethod
    def credentials_save(cls, credentials):
        """Given login credentials (Blender-ID username and password), we use the
        authenticate function to generate the token, which we store in the profiles.json.
        Currently we overwrite all credentials with the new one if succesful.
        """
        authentication = cls.authenticate(
            credentials['username'], credentials['password'])
        if authentication['authenticated']:
            import json
            profiles_file = cls.get_profiles_file()
            with open(profiles_file, 'w') as outfile:
                json.dump([{
                    "username" : credentials['username'],
                    "token" : authentication['token'],
                    "is_active" : True}], outfile)
        return dict(message=authentication['message'])

    @classmethod
    def get_active_profile(cls):
        """Pick the active profile from the profiles.json. If no active profile is found
        we return None.
        """
        profiles = ProfilesUtility.credentials_load()
        index = next((index for (index, d) in enumerate(profiles) if d["is_active"] == True), None)
        if index is not None:
            return profiles[index]
        else:
            return None


class BlenderIdPreferences(AddonPreferences):
    bl_idname = __name__

    profile = ProfilesUtility.get_active_profile()
    print(profile)
    if profile:
        username = profile['username']
    else:
        username = ""
    blender_id_username = StringProperty(
        name="Username",
        default=username,
        options={'HIDDEN', 'SKIP_SAVE'})

    blender_id_password = StringProperty(
        name="Password",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD')

    def draw(self, context):
        layout = self.layout
        if self.username != "":
            text = "You are logged in as {0}".format(self.username)
            layout.label(text=text, icon='WORLD_DATA')
        else:
            layout.prop(self, "blender_id_username")
            layout.prop(self, "blender_id_password")
            layout.operator("blender_id.save_credentials")


class BlenderIdSaveCredentials(bpy.types.Operator):
    bl_idname = "blender_id.save_credentials"
    bl_label = "Save credentials"
    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences
        credentials = dict(
            username=addon_prefs.blender_id_username,
            password=addon_prefs.blender_id_password)
        try:
            r = ProfilesUtility.credentials_save(credentials)
        except Exception:
            self.report({'ERROR'}, "Can't connect to {0}".format(
                SystemUtility.blender_id_endpoint()))

        return{'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
