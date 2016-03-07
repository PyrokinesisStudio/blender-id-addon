import os
import json
import bpy

profiles_path = bpy.utils.user_resource('CONFIG', "blender_id", create=True)
profiles_file = os.path.join(profiles_path, 'profiles.json')


def _create_default_file():
    """Creates the default profile file, returning its contents."""

    profiles_default_data = {
        'active_profile': None,
        'profiles': {}
    }

    os.makedirs(profiles_path, exist_ok=True)

    # Populate the file, ensuring that its permissions are restrictive enough.
    old_umask = os.umask(0o077)
    try:
        with open(profiles_file, 'w') as outfile:
            json.dump(profiles_default_data, outfile)
    finally:
        os.umask(old_umask)

    return profiles_default_data


def get_profiles_data():
    """Returns the profiles.json content from a blender_id folder in the
    Blender config directory. If the file does not exist we create one with the
    basic data structure.
    """

    # if the file does not exist
    if not os.path.exists(profiles_file):
        return _create_default_file()

    # try parsing the file
    with open(profiles_file, 'r') as f:
        try:
            file_data = json.load(f)
            file_data['active_profile']
            file_data['profiles']
            return file_data
        except (ValueError,  # malformed json data
                KeyError):  # it doesn't have the expected content
            print("(%s) "
                  "Warning: profiles.json is either empty or malformed. "
                  "The file will be reset." % __name__)

            # overwrite the file
            return _create_default_file()


def get_active_user_id():
    """Get the id of the currently active profile. If there is no
    active profile on the file, this function will return None.
    """

    return get_profiles_data()['active_profile']


def get_active_profile():
    """Pick the active profile from profiles.json. If there is no
    active profile on the file, this function will return None.
    """
    file_content = get_profiles_data()
    user_id = file_content['active_profile']
    if not user_id or user_id not in file_content['profiles']:
        return None

    profile = file_content['profiles'][user_id]
    profile['user_id'] = user_id
    return profile


def get_profile(user_id):
    """Loads the profile data for a given user_id if existing
    else it returns None.
    """

    file_content = get_profiles_data()
    if not user_id or user_id not in file_content['profiles']:
        return None

    profile = file_content['profiles'][user_id]
    return dict(
        username=profile['username'],
        token=profile['token']
    )


def save_as_active_profile(user_id, token, username):
    """Saves a new profile and marks it as the active one
    """

    profiles = get_profiles_data()['profiles']
    # overwrite or create new profile entry for this user_id
    profiles[user_id] = dict(
        username=username,
        token=token
    )
    with open(profiles_file, 'w') as outfile:
        json.dump({
            'active_profile': user_id,
            'profiles': profiles
        }, outfile)


def logout(user_id):
    """Invalidates the token and state of active for this user.
    This is different from switching the active profile, where the active
    profile is changed but there isn't an explicit logout.
    """

    file_content = get_profiles_data()

    # Remove user from 'active profile'
    if file_content['active_profile'] == user_id:
        file_content['active_profile'] = ""

    # Remove both user and token from profiles list
    if user_id in file_content['profiles']:
        del file_content['profiles'][user_id]

    with open(profiles_file, 'w') as outfile:
        json.dump(file_content, outfile)
