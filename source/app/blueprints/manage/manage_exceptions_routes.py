#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_wtf import FlaskForm

from app.iris_engine.utils.postprocessor import postprocessor_delete
from app.iris_engine.utils.postprocessor import postprocessor_get
from app.iris_engine.utils.postprocessor import postprocessor_patch
from app.iris_engine.utils.postprocessor import postprocessor_post
from app.iris_engine.utils.postprocessor import postprocessor_put
from app.iris_engine.utils.tracker import track_activity
from app.models.authorization import Permissions
from app.util import ac_api_requires
from app.util import ac_requires
from app.util import response_error
from app.util import response_success

manage_exceptions_blueprint = Blueprint(
    'manage_exceptions',
    __name__,
    template_folder='templates'
)


def _proxy_error(resp_data):
    msg = resp_data.get('detail', resp_data.get('message', 'Unknown error from postprocessor'))
    return response_error(f'Postprocessor error: {msg}')


@manage_exceptions_blueprint.route('/manage/exceptions')
@ac_requires(Permissions.standard_user, no_cid_required=True)
def manage_exceptions_index(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_exceptions.manage_exceptions_index', cid=caseid))
    form = FlaskForm()
    return render_template('manage_exceptions.html', form=form)


@manage_exceptions_blueprint.route('/manage/exceptions/list', methods=['GET'])
@ac_api_requires(Permissions.standard_user)
def list_exceptions():
    params = {}
    for key in ('tenant_key', 'q', 'page', 'per_page', 'sort_by', 'sort_dir'):
        val = request.args.get(key)
        if val:
            params[key] = val

    resp, err = postprocessor_get('/exceptions', params=params)
    if err:
        return err

    if resp.status_code == 200:
        return response_success("", data=resp.json())

    return _proxy_error(resp.json())


@manage_exceptions_blueprint.route('/manage/exceptions/tenants', methods=['GET'])
@ac_api_requires(Permissions.standard_user)
def list_exception_tenants():
    resp, err = postprocessor_get('/exceptions/tenants')
    if err:
        return err

    if resp.status_code == 200:
        return response_success("", data=resp.json())

    return _proxy_error(resp.json())


@manage_exceptions_blueprint.route('/manage/exceptions/stats', methods=['GET'])
@ac_api_requires(Permissions.standard_user)
def get_exception_stats():
    params = {}
    tenant_key = request.args.get('tenant_key')
    if tenant_key:
        params['tenant_key'] = tenant_key

    resp, err = postprocessor_get('/exceptions/stats', params=params)
    if err:
        return err

    if resp.status_code == 200:
        return response_success("", data=resp.json())

    return _proxy_error(resp.json())


@manage_exceptions_blueprint.route('/manage/exceptions/add', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def add_exception():
    js_data = request.get_json()
    if not js_data:
        return response_error('Invalid request data')

    resp, err = postprocessor_post('/exceptions', json_data=js_data)
    if err:
        return err

    resp_data = resp.json()
    if resp.status_code == 201 or resp_data.get('status') == 'success':
        track_activity("created alert exception via manage page", ctx_less=True)
        return response_success("Exception created successfully", data=resp_data.get('exception', resp_data))

    return _proxy_error(resp_data)


@manage_exceptions_blueprint.route('/manage/exceptions/update/<string:exception_id>', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def update_exception(exception_id):
    js_data = request.get_json()
    if not js_data:
        return response_error('Invalid request data')

    resp, err = postprocessor_put(f'/exceptions/{exception_id}', json_data=js_data)
    if err:
        return err

    resp_data = resp.json()
    if resp.status_code == 200 or resp_data.get('status') == 'success':
        track_activity(f"updated alert exception {exception_id}", ctx_less=True)
        return response_success("Exception updated successfully", data=resp_data.get('exception', resp_data))

    return _proxy_error(resp_data)


@manage_exceptions_blueprint.route('/manage/exceptions/extend/<string:exception_id>', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def extend_exception(exception_id):
    js_data = request.get_json()
    if not js_data:
        return response_error('Invalid request data')

    resp, err = postprocessor_patch(f'/exceptions/{exception_id}/extend', json_data=js_data)
    if err:
        return err

    resp_data = resp.json()
    if resp.status_code == 200 or resp_data.get('status') == 'success':
        track_activity(f"extended alert exception {exception_id}", ctx_less=True)
        return response_success("Exception extended successfully", data=resp_data.get('exception', resp_data))

    return _proxy_error(resp_data)


@manage_exceptions_blueprint.route('/manage/exceptions/delete/<string:exception_id>', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def delete_exception(exception_id):
    resp, err = postprocessor_delete(f'/exceptions/{exception_id}')
    if err:
        return err

    if resp.status_code in (200, 204):
        track_activity(f"deleted alert exception {exception_id}", ctx_less=True)
        return response_success("Exception deleted successfully")

    resp_data = resp.json()
    return _proxy_error(resp_data)


@manage_exceptions_blueprint.route('/manage/exceptions/bulk-delete', methods=['POST'])
@ac_api_requires(Permissions.server_administrator)
def bulk_delete_exceptions():
    js_data = request.get_json()
    if not js_data:
        return response_error('Invalid request data')

    resp, err = postprocessor_post('/exceptions/bulk-delete', json_data=js_data)
    if err:
        return err

    resp_data = resp.json()
    if resp.status_code == 200 or resp_data.get('status') == 'success':
        track_activity("bulk-deleted alert exceptions", ctx_less=True)
        return response_success("Exceptions deleted successfully", data=resp_data)

    return _proxy_error(resp_data)
