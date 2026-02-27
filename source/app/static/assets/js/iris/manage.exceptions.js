var exceptions_table = null;

function format_criteria_badges(criteria) {
    if (!criteria) return '<span class="text-muted">None</span>';
    var html = '';

    if (criteria.rule_id) {
        var ids = Array.isArray(criteria.rule_id) ? criteria.rule_id : [criteria.rule_id];
        ids.forEach(function (id) {
            html += '<span class="badge badge-primary mr-1">rule:' + sanitizeHTML(String(id)) + '</span>';
        });
    }
    if (criteria.agent_name) {
        var agents = Array.isArray(criteria.agent_name) ? criteria.agent_name : [criteria.agent_name];
        agents.forEach(function (a) {
            html += '<span class="badge badge-info mr-1">agent:' + sanitizeHTML(a) + '</span>';
        });
    }
    if (criteria.case_tags) {
        var tags = Array.isArray(criteria.case_tags) ? criteria.case_tags : [criteria.case_tags];
        tags.forEach(function (t) {
            html += '<span class="badge badge-secondary mr-1">tag:' + sanitizeHTML(t) + '</span>';
        });
    }
    return html || '<span class="text-muted">None</span>';
}

function format_ttl_remaining(row) {
    if (row.ttl_remaining_seconds !== undefined && row.ttl_remaining_seconds !== null) {
        var secs = row.ttl_remaining_seconds;
        if (secs <= 0) return '<span class="text-danger">Expired</span>';
        var hours = Math.floor(secs / 3600);
        var days = Math.floor(hours / 24);
        var remHours = hours % 24;
        if (days > 0) {
            return days + 'd ' + remHours + 'h';
        }
        return hours + 'h';
    }
    if (row.expires_at) {
        var exp = new Date(row.expires_at);
        var now = new Date();
        var diff = exp - now;
        if (diff <= 0) return '<span class="text-danger">Expired</span>';
        var hrs = Math.floor(diff / 3600000);
        var d = Math.floor(hrs / 24);
        var rh = hrs % 24;
        if (d > 0) return d + 'd ' + rh + 'h';
        return hrs + 'h';
    }
    return '-';
}

function format_datetime(dt) {
    if (!dt) return '-';
    try {
        var d = new Date(dt);
        return d.toLocaleString();
    } catch (e) {
        return sanitizeHTML(String(dt));
    }
}

function init_exceptions_table() {
    if (exceptions_table) {
        exceptions_table.destroy();
        exceptions_table = null;
    }

    var cid = case_param();

    exceptions_table = $('#exceptions_table').DataTable({
        ajax: {
            url: '/manage/exceptions/list' + cid,
            type: 'GET',
            data: function (d) {
                var tenant = $('#filter_tenant').val();
                var search = $('#filter_search').val();
                if (tenant) d.tenant_key = tenant;
                if (search) d.q = search;
                return d;
            },
            dataSrc: function (json) {
                if (json && json.status === 'success' && json.data) {
                    var data = json.data;
                    if (Array.isArray(data)) return data;
                    if (data.exceptions && Array.isArray(data.exceptions)) return data.exceptions;
                    if (data.items && Array.isArray(data.items)) return data.items;
                }
                return [];
            }
        },
        order: [[7, 'desc']],
        autoWidth: false,
        pageLength: 25,
        columns: [
            {
                data: null,
                orderable: false,
                render: function (data, type, row) {
                    var id = row.id || row.exception_id || '';
                    return '<input type="checkbox" class="exception-select" data-id="' + sanitizeHTML(String(id)) + '">';
                }
            },
            {
                data: 'tenant_key',
                render: function (data, type) {
                    if (type === 'display') return sanitizeHTML(data || '');
                    return data;
                }
            },
            {
                data: 'criteria',
                orderable: false,
                render: function (data, type) {
                    if (type === 'display') return format_criteria_badges(data);
                    return JSON.stringify(data);
                }
            },
            {
                data: 'duration_hours',
                render: function (data, type) {
                    if (type === 'display') return data ? data + 'h' : '-';
                    return data;
                }
            },
            {
                data: null,
                orderable: false,
                render: function (data, type, row) {
                    if (type === 'display') return format_ttl_remaining(row);
                    return '';
                }
            },
            {
                data: 'reason',
                render: function (data, type) {
                    if (type === 'display') {
                        var text = sanitizeHTML(data || '');
                        if (text.length > 60) return '<span title="' + text + '">' + text.substring(0, 60) + '...</span>';
                        return text || '<span class="text-muted">-</span>';
                    }
                    return data;
                }
            },
            {
                data: 'created_by',
                render: function (data, type) {
                    if (type === 'display') return sanitizeHTML(data || '-');
                    return data;
                }
            },
            {
                data: 'created_at',
                render: function (data, type) {
                    if (type === 'display') return format_datetime(data);
                    return data;
                }
            },
            {
                data: null,
                orderable: false,
                render: function (data, type, row) {
                    var id = row.id || row.exception_id || '';
                    return '<div class="btn-group btn-group-sm">' +
                        '<button class="btn btn-outline-primary btn-sm" onclick="edit_exception(\'' + id + '\');" title="Edit"><i class="fa fa-pen"></i></button>' +
                        '<button class="btn btn-outline-info btn-sm" onclick="extend_exception(\'' + id + '\');" title="Extend TTL"><i class="fa fa-clock"></i></button>' +
                        '<button class="btn btn-outline-danger btn-sm" onclick="delete_exception(\'' + id + '\');" title="Delete"><i class="fa fa-trash"></i></button>' +
                        '</div>';
                }
            }
        ]
    });
}

function refresh_exception_table(do_notify) {
    if (exceptions_table) {
        exceptions_table.ajax.reload();
    } else {
        init_exceptions_table();
    }
    if (do_notify) {
        notify_success("Refreshed");
    }
}

function load_exception_stats() {
    var cid = case_param();
    var tenant = $('#filter_tenant').val();
    var url = '/manage/exceptions/stats' + cid;
    if (tenant) url += '&tenant_key=' + encodeURIComponent(tenant);

    get_request_api(url)
    .done(function (data) {
        if (data && data.status === 'success' && data.data) {
            var stats = data.data;
            $('#stat_total').text(stats.total !== undefined ? stats.total : (stats.total_exceptions !== undefined ? stats.total_exceptions : '-'));
            $('#stat_tenants').text(stats.tenants !== undefined ? stats.tenants : (stats.tenant_count !== undefined ? stats.tenant_count : '-'));
            $('#stat_expiring').text(stats.expiring_soon !== undefined ? stats.expiring_soon : '-');
        }
    })
    .fail(function () {
        $('#stat_total').text('-');
        $('#stat_tenants').text('-');
        $('#stat_expiring').text('-');
    });
}

function load_tenant_filter() {
    var cid = case_param();
    get_request_api('/manage/exceptions/tenants' + cid)
    .done(function (data) {
        if (data && data.status === 'success' && data.data) {
            var tenants = data.data;
            if (!Array.isArray(tenants) && tenants.tenants) tenants = tenants.tenants;
            var $sel = $('#filter_tenant');
            $sel.find('option:not(:first)').remove();
            if (Array.isArray(tenants)) {
                tenants.forEach(function (t) {
                    var name = (typeof t === 'string') ? t : (t.tenant_key || t.name || t);
                    $sel.append('<option value="' + sanitizeHTML(String(name)) + '">' + sanitizeHTML(String(name)) + '</option>');
                });
            }
        }
    });
}

function reset_modal_to_create() {
    $('#exception_modal_title').text('Add Exception');
    $('#exception_form_main').show();
    $('#exception_form_extend').hide();
    $('#exception_id').val('');
    $('#exception_mode').val('create');
    $('#exception_tenant_key').val('').prop('readonly', false);
    $('#exception_rule_id').val('');
    $('#exception_agent_name').val('');
    $('#exception_case_tags').val('');
    $('#exception_duration').val(168);
    $('#exception_reason').val('');
    $('#exception_created_by').val('');
    $('#btn_delete_from_modal').hide();
    $('#btn_submit_exception').text('Save').show();
}

function add_exception() {
    reset_modal_to_create();
    $('#modal_exception').modal({show: true});
}

function edit_exception(id) {
    reset_modal_to_create();
    $('#exception_modal_title').text('Edit Exception');
    $('#exception_mode').val('edit');
    $('#exception_id').val(id);
    $('#btn_delete_from_modal').show().attr('onclick', "delete_exception('" + id + "');");
    $('#btn_submit_exception').text('Update');

    var cid = case_param();
    get_request_api('/manage/exceptions/list' + cid + '&id=' + encodeURIComponent(id))
    .done(function (data) {
        if (data && data.status === 'success' && data.data) {
            var items = data.data;
            var exc = null;
            if (Array.isArray(items)) {
                exc = items.find(function (e) { return (e.id || e.exception_id) === id; });
            } else if (items.exceptions) {
                exc = items.exceptions.find(function (e) { return (e.id || e.exception_id) === id; });
            } else if (items.id || items.exception_id) {
                exc = items;
            }
            if (exc) {
                populate_form_from_exception(exc);
            }
        }
        $('#modal_exception').modal({show: true});
    })
    .fail(function () {
        $('#modal_exception').modal({show: true});
    });
}

function populate_form_from_exception(exc) {
    $('#exception_tenant_key').val(exc.tenant_key || '');
    if (exc.criteria) {
        var c = exc.criteria;
        if (c.rule_id) {
            var ids = Array.isArray(c.rule_id) ? c.rule_id.join(', ') : String(c.rule_id);
            $('#exception_rule_id').val(ids);
        }
        if (c.agent_name) {
            var agents = Array.isArray(c.agent_name) ? c.agent_name.join(', ') : c.agent_name;
            $('#exception_agent_name').val(agents);
        }
        if (c.case_tags) {
            var tags = Array.isArray(c.case_tags) ? c.case_tags.join(', ') : c.case_tags;
            $('#exception_case_tags').val(tags);
        }
    }
    $('#exception_duration').val(exc.duration_hours || 168);
    $('#exception_reason').val(exc.reason || '');
    $('#exception_created_by').val(exc.created_by || '');
}

function extend_exception(id) {
    $('#exception_modal_title').text('Extend Exception TTL');
    $('#exception_form_main').hide();
    $('#exception_form_extend').show();
    $('#extend_exception_id').val(id);
    $('#extend_additional_hours').val(168);
    $('#btn_delete_from_modal').hide();
    $('#btn_submit_exception').text('Extend').show();
    $('#exception_mode').val('extend');
    $('#modal_exception').modal({show: true});
}

function submit_manage_exception() {
    var mode = $('#exception_mode').val();

    if (mode === 'extend') {
        submit_extend_exception();
        return;
    }

    var tenantKey = $('#exception_tenant_key').val().trim();
    if (!tenantKey) {
        notify_error('Tenant Key is required');
        return;
    }

    var ruleId = $('#exception_rule_id').val().trim();
    var agentName = $('#exception_agent_name').val().trim();
    var caseTags = $('#exception_case_tags').val().trim();

    if (!ruleId && !agentName && !caseTags) {
        notify_error('At least one criteria field is required');
        return;
    }

    var criteria = {};
    if (ruleId) {
        criteria.rule_id = ruleId.includes(',') ? ruleId.split(',').map(function (s) { return s.trim(); }).filter(Boolean) : ruleId;
    }
    if (agentName) criteria.agent_name = agentName;
    if (caseTags) {
        criteria.case_tags = caseTags.includes(',') ? caseTags.split(',').map(function (s) { return s.trim(); }).filter(Boolean) : caseTags;
    }

    var payload = {
        tenant_key: tenantKey,
        criteria: criteria,
        duration_hours: parseInt($('#exception_duration').val()) || 168,
        reason: $('#exception_reason').val().trim(),
        created_by: $('#exception_created_by').val().trim(),
        csrf_token: $('#csrf_token').val()
    };

    var exceptionId = $('#exception_id').val();
    var url, successMsg;
    if (mode === 'edit' && exceptionId) {
        url = '/manage/exceptions/update/' + encodeURIComponent(exceptionId);
        successMsg = 'Exception updated';
    } else {
        url = '/manage/exceptions/add';
        successMsg = 'Exception created';
    }

    $('#btn_submit_exception').prop('disabled', true).text('Saving...');

    post_request_api(url, JSON.stringify(payload), true)
    .done(function (data) {
        if (notify_auto_api(data)) {
            $('#modal_exception').modal('hide');
            refresh_exception_table();
            load_exception_stats();
        }
    })
    .always(function () {
        $('#btn_submit_exception').prop('disabled', false).text(mode === 'edit' ? 'Update' : 'Save');
    });
}

function submit_extend_exception() {
    var id = $('#extend_exception_id').val();
    var hours = parseInt($('#extend_additional_hours').val());
    if (!hours || hours < 1) {
        notify_error('Additional hours must be at least 1');
        return;
    }

    var payload = { additional_hours: hours, csrf_token: $('#csrf_token').val() };

    $('#btn_submit_exception').prop('disabled', true).text('Extending...');

    post_request_api('/manage/exceptions/extend/' + encodeURIComponent(id), JSON.stringify(payload), true)
    .done(function (data) {
        if (notify_auto_api(data)) {
            $('#modal_exception').modal('hide');
            refresh_exception_table();
            load_exception_stats();
        }
    })
    .always(function () {
        $('#btn_submit_exception').prop('disabled', false).text('Extend');
    });
}

function delete_exception(id) {
    swal({
        title: "Are you sure?",
        text: "This exception will be permanently deleted.",
        icon: "warning",
        buttons: true,
        dangerMode: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    })
    .then(function (willDelete) {
        if (willDelete) {
            post_request_api('/manage/exceptions/delete/' + encodeURIComponent(id))
            .done(function (data) {
                if (notify_auto_api(data)) {
                    $('#modal_exception').modal('hide');
                    refresh_exception_table();
                    load_exception_stats();
                }
            });
        }
    });
}

function bulk_delete_exceptions() {
    var ids = [];
    $('.exception-select:checked').each(function () {
        ids.push($(this).data('id'));
    });
    if (ids.length === 0) {
        notify_error('No exceptions selected');
        return;
    }
    swal({
        title: "Delete " + ids.length + " exception(s)?",
        text: "This action cannot be undone.",
        icon: "warning",
        buttons: true,
        dangerMode: true,
    })
    .then(function (willDelete) {
        if (willDelete) {
            post_request_api('/manage/exceptions/bulk-delete', JSON.stringify({ ids: ids, csrf_token: $('#csrf_token').val() }), true)
            .done(function (data) {
                if (notify_auto_api(data)) {
                    refresh_exception_table();
                    load_exception_stats();
                    update_bulk_delete_visibility();
                }
            });
        }
    });
}

function update_bulk_delete_visibility() {
    var checked = $('.exception-select:checked').length;
    if (checked > 0) {
        $('#btn_bulk_delete').show();
    } else {
        $('#btn_bulk_delete').hide();
    }
}

$(document).ready(function () {
    init_exceptions_table();
    load_exception_stats();
    load_tenant_filter();

    $('#filter_tenant').on('change', function () {
        refresh_exception_table();
        load_exception_stats();
    });

    var searchTimeout;
    $('#filter_search').on('keyup', function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
            refresh_exception_table();
        }, 400);
    });

    $(document).on('change', '#select_all_exceptions', function () {
        var checked = $(this).prop('checked');
        $('.exception-select').prop('checked', checked);
        update_bulk_delete_visibility();
    });

    $(document).on('change', '.exception-select', function () {
        update_bulk_delete_visibility();
        var allChecked = $('.exception-select').length === $('.exception-select:checked').length;
        $('#select_all_exceptions').prop('checked', allChecked);
    });
});
