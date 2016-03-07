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
    "author": "Francesco Siddi, Inês Almeida and Sybren A. Stüvel",
    "version": (0, 1, 0),
    "blender": (2, 76, 0),
    "location": "Add-on preferences",
    "description":
        "Stores your Blender ID credentials for usage with other add-ons",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/System/BlenderID",
    "category": "System",
    "support": "TESTING"
}

import random
import string

import bpy
from bpy.types import AddonPreferences
from bpy.types import Operator
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from bpy.props import PointerProperty

from . import api, profiles


class BlenderIdPreferences(AddonPreferences):
    bl_idname = __name__

    p_username = ''
    profile = profiles.get_active_profile()
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

        if active_profile.unique_id != "":
            text = "You are logged in as {0}".format(self.blender_id_username)
            layout.label(text=text, icon='WORLD_DATA')
            layout.operator('blender_id.logout')
        else:
            if self.error_message:
                sub = layout.row()
                sub.alert = True  # labels don't display in red :(
                sub.label(self.error_message, icon="ERROR")
            layout.prop(self, 'blender_id_username')
            layout.prop(self, 'blender_id_password')
            layout.operator('blender_id.login')


class BlenderIdLogin(Operator):
    bl_idname = 'blender_id.login'
    bl_label = 'Login'

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__name__].preferences
        active_profile = context.window_manager.blender_id_active_profile

        resp = api.blender_id_server_authenticate(
            username=addon_prefs.blender_id_username,
            password=addon_prefs.blender_id_password
        )

        if resp['status'] == "success":
            active_profile.unique_id = resp['user_id']
            active_profile.token = resp['token']

            # Prevent saving the password in user preferences. Overwrite the password with a
            # random string, as just setting to '' might only replace the first byte with 0.
            pwlen = len(addon_prefs.blender_id_password)
            rnd = ''.join(random.choice(string.ascii_uppercase + string.digits)
                          for _ in range(pwlen + 16))
            addon_prefs.blender_id_password = rnd
            addon_prefs.blender_id_password = ''

            profiles.save_as_active_profile(
                resp['user_id'],
                resp['token'],
                addon_prefs.blender_id_username
            )
        else:
            addon_prefs.error_message = resp['error_message']
        return {'FINISHED'}


class BlenderIdLogout(Operator):
    bl_idname = 'blender_id.logout'
    bl_label = 'Logout'

    def execute(self, context):
        addon_prefs = context.user_preferences.addons[__name__].preferences
        active_profile = context.window_manager.blender_id_active_profile

        api.blender_id_server_logout(active_profile.unique_id,
                                     active_profile.token)

        profiles.logout(active_profile.unique_id)
        active_profile.unique_id = ""
        active_profile.token = ""
        addon_prefs.error_message = ""

        return {'FINISHED'}


class BlenderIdProfile(PropertyGroup):
    profile = profiles.get_active_profile()
    if profile:
        p_user_id = profile['user_id']
        p_token = profile['token']
    else:
        p_user_id = ""
        p_token = ""

    unique_id = StringProperty(
        name='ID',
        default=p_user_id,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    token = StringProperty(
        name='Token',
        default=p_token,
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
