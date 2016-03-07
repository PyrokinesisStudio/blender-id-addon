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

# <pep8 compliant>

import requests
import requests.exceptions
import socket
import os


def blender_id_endpoint():
    """Gets the endpoint for the authentication API. If the BLENDER_ID_ENDPOINT env variable
    is defined, it's possible to override the (default) production address.
    """
    return os.environ.get(
        'BLENDER_ID_ENDPOINT',
        'https://www.blender.org/id'
    ).rstrip('/')


def blender_id_server_authenticate(username, password):
    """Authenticate the user with the server with a single transaction
    containing username and password (must happen via HTTPS).

    If the transaction is successful, status will be 'successful' and we
    return the user's unique blender id and a token (that will be used to
    represent that username and password combination).
    If there was a problem, status will be 'fail' and we return an error
    message. Problems may be with the connection or wrong user/password.
    """

    payload = dict(
        username=username,
        password=password,
        host_label='Blender running on %r' % socket.gethostname()
    )
    try:
        r = requests.post("{0}/u/identify".format(blender_id_endpoint()),
                          data=payload, verify=True)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        return dict(
            status='fail',
            user_id=None,
            token=None,
            error_message=str(e)
        )

    user_id = None
    token = None
    error_message = None

    if r.status_code == 200:
        resp = r.json()
        status = resp['status']
        if status == 'success':
            user_id = str(resp['data']['user_id'])
            # We just use the access token for now.
            token = resp['data']['oauth_token']['access_token']
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


def blender_id_server_logout(user_id, token):
    """Logs out of the Blender ID service by removing the token server-side.

    @param user_id: the email address of the user.
    @type user_id: str
    @param token: the token to remove
    @type token: str
    @return: {'status': 'fail' or 'success', 'error_message': str}
    @rtype: dict
    """

    payload = dict(
        user_id=user_id,
        token=token
    )
    try:
        r = requests.post("{0}/u/delete_token".format(blender_id_endpoint()),
                          data=payload, verify=True)
    except (requests.exceptions.SSLError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError) as e:
        return dict(
            status='fail',
            error_message=format("There was a problem setting up a connection to "
                                 "the server. Error type is: %s" % type(e).__name__)
        )

    if r.status_code != 200:
        return dict(
            status='fail',
            error_message=format("There was a problem communicating with"
                                 " the server. Error code is: %s" % r.status_code)
        )

    resp = r.json()
    return dict(
        status=resp['status'],
        error_message=None
    )
