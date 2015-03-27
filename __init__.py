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
import json
import requests

from bpy.props import StringProperty
from bpy.types import AddonPreferences

class ProfilesUtility():
    def get_profiles_file():
        profiles_path = os.path.join(os.path.expanduser('~'), '.blender_id')
        profiles_file = os.path.join(profiles_path, 'profiles.json')
        if not os.path.exists(profiles_file):
            profiles = dict(username='', password='')
            os.makedirs(profiles_path)
            with open(profiles_file, 'w') as outfile:
                json.dump(profiles, outfile)
        return profiles_file

    def authenticate(username, password):
        payload = dict(username=username, password=password)
        r = requests.post("http://localhost:8000/u/identify", data=payload)
        message = r.json()['message']
        if r.status_code == 200:
            authenticated = True
        else:
            authenticated = False
        return dict(authenticated=authenticated, message=message)

    @classmethod
    def credentials_load(cls):
        """Loads the credentials from a profile file. TODO: add a username arg
        so that one out of many identities can be retrieved.
        """

        profiles_file = cls.get_profiles_file()
        with open(profiles_file) as outfile:
            return json.load(outfile)

    @classmethod
    def credentials_save(cls, credentials):
        authentication = cls.authenticate(credentials['username'], credentials['password'])
        if authentication['authenticated']:
            profiles_file = cls.get_profiles_file()
            with open(profiles_file, 'w') as outfile:
                json.dump(credentials, outfile)
        return dict(message=authentication['message'])


class BlenderIdPreferences(AddonPreferences):
    bl_idname = __name__

    profiles = ProfilesUtility.credentials_load()
    blender_id_username = StringProperty(
        name="Username",
        default=profiles['username'],
        options={'HIDDEN', 'SKIP_SAVE'})

    blender_id_password = StringProperty(
        name="Password",
        default=profiles['username'],
        options={'HIDDEN', 'SKIP_SAVE'},
        subtype='PASSWORD')

    def draw(self, context):
        layout = self.layout
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
        r = ProfilesUtility.credentials_save(credentials)
        return{'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
