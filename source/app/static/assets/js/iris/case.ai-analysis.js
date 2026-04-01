/* AI Analysis modal logic — proxied through IRIS Flask backend */

var LS_MODEL_KEY  = 'iris_ai_analysis_last_model';
var LS_TIER_KEY   = 'iris_ai_analysis_last_tier';
var LS_TENANT_KEY = 'iris_ai_analysis_last_tenant';

var _elapsedInterval = null;
var _elapsedStart    = null;

/* ------------------------------------------------------------------ */
/*  Entry point — called by the toolbar button                        */
/* ------------------------------------------------------------------ */
function openAiAnalysisModal() {
    $('#ai_models_loading').show();
    $('#ai_models_error').hide();
    $('#ai_form_panel').hide();
    $('#ai_progress_panel').hide();
    $('#ai_result_panel').hide();
    $('#ai_result_success').hide();
    $('#ai_result_error').hide();
    $('#btn_run_ai_analysis').prop('disabled', false).show();
    $('#modal_ai_analysis').modal('show');
    _loadModels();
}

/* ------------------------------------------------------------------ */
/*  Fetch models via IRIS proxy                                       */
/* ------------------------------------------------------------------ */
function _loadModels() {
    get_request_api('/case/ai/models')
    .done(function(data) {
        $('#ai_models_loading').hide();
        if (data.status === 'success' && data.data) {
            _populateModelSelect(data.data);
            _restorePreferences(data.data);
            $('#ai_form_panel').show();
        } else {
            var msg = data.message || 'Failed to load AI models';
            $('#ai_models_error').text(msg).show();
        }
    })
    .fail(function(jqXHR) {
        $('#ai_models_loading').hide();
        var msg = 'Unable to reach AI Agent service';
        if (jqXHR.responseJSON && jqXHR.responseJSON.message) {
            msg = jqXHR.responseJSON.message;
        }
        $('#ai_models_error').text(msg).show();
    });
}

/* ------------------------------------------------------------------ */
/*  Build <option> groups in the model selector                       */
/* ------------------------------------------------------------------ */
function _populateModelSelect(data) {
    var $sel = $('#ai_model_select').empty();
    var grouped = {};

    $.each(data.models || [], function (_, m) {
        var key = m.provider || 'unknown';
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(m);
    });

    $.each(grouped, function (provider, models) {
        var status = null;
        $.each(data.providers || [], function (_, p) {
            if (p.provider === provider) { status = p; return false; }
        });
        var label = provider;
        if (status && !status.reachable) label += ' (unreachable)';

        var $grp = $('<optgroup>').attr('label', label);
        $.each(models, function (_, m) {
            var val = m.provider + '::' + m.id;
            var txt = m.display_name || m.id;
            var $opt = $('<option>').val(val).text(txt);
            $opt.data('provider-kind', m.provider_kind || '');
            if (status && !status.reachable) $opt.prop('disabled', true);
            $grp.append($opt);
        });
        $sel.append($grp);
    });

    $sel.off('change.ai').on('change.ai', function () {
        var kind = $sel.find(':selected').data('provider-kind') || '';
        var prov = ($sel.val() || '').split('::')[0];
        $('#ai_provider_label').text(prov + (kind ? ' (' + kind + ')' : ''));
    });
}

/* ------------------------------------------------------------------ */
/*  Restore user preferences from localStorage                       */
/* ------------------------------------------------------------------ */
function _restorePreferences(data) {
    var lastModel  = localStorage.getItem(LS_MODEL_KEY);
    var lastTier   = localStorage.getItem(LS_TIER_KEY);
    var lastTenant = localStorage.getItem(LS_TENANT_KEY);

    if (lastModel && $('#ai_model_select option[value="' + lastModel + '"]').length) {
        $('#ai_model_select').val(lastModel);
    } else if (data.default_provider && data.default_model) {
        var def = data.default_provider + '::' + data.default_model;
        if ($('#ai_model_select option[value="' + def + '"]').length) {
            $('#ai_model_select').val(def);
        }
    }

    if (lastTier) {
        $('#ai_tier_select').val(lastTier);
    }

    var $ctx = $('#ai_case_context');
    var clientName = $ctx.data('client-name') || '';
    $('#ai_tenant_id').val(lastTenant || clientName);

    if (!$('#ai_directive').val()) {
        $('#ai_directive').val(
            'Investigate all IOCs and correlate alerts. ' +
            'Identify the source and scope of compromise.'
        );
    }

    $('#ai_model_select').trigger('change.ai');
}

/* ------------------------------------------------------------------ */
/*  Persist current selections                                        */
/* ------------------------------------------------------------------ */
function _savePreferences() {
    localStorage.setItem(LS_MODEL_KEY,  $('#ai_model_select').val() || '');
    localStorage.setItem(LS_TIER_KEY,   $('#ai_tier_select').val()  || '');
    localStorage.setItem(LS_TENANT_KEY, $('#ai_tenant_id').val()    || '');
}

/* ------------------------------------------------------------------ */
/*  Submit analysis request via IRIS proxy                            */
/* ------------------------------------------------------------------ */
function runAiAnalysis() {
    var modelVal = $('#ai_model_select').val();
    if (!modelVal) { notify_error('Please select a model'); return; }

    var tenantId = $('#ai_tenant_id').val().trim();
    if (!tenantId) { notify_error('Tenant ID is required'); return; }

    _savePreferences();

    var parts    = modelVal.split('::');
    var provider = parts[0];
    var modelId  = parts.slice(1).join('::');

    var payload = {
        tenant_id: tenantId,
        tier:      $('#ai_tier_select').val() || 'standard',
        provider:  provider,
        model:     modelId,
        csrf_token: $('#csrf_token').val()
    };

    var directive = $('#ai_directive').val().trim();
    if (directive) payload.directive = directive;

    $('#ai_form_panel').hide();
    $('#ai_result_panel').hide();
    $('#btn_run_ai_analysis').prop('disabled', true);
    $('#ai_progress_panel').show();
    _startElapsedTimer();

    post_request_api('/case/ai/analyze', JSON.stringify(payload))
    .done(function(data) {
        _stopElapsedTimer();
        if (data.status === 'success' && data.data) {
            _showResult(data.data);
        } else {
            $('#ai_progress_panel').hide();
            $('#ai_result_panel').show();
            $('#ai_result_success').hide();
            $('#ai_result_error').show();
            $('#ai_result_error_msg').text(data.message || 'Analysis failed');
            $('#btn_run_ai_analysis').prop('disabled', false);
        }
    })
    .fail(function(jqXHR) {
        _stopElapsedTimer();
        $('#ai_progress_panel').hide();
        $('#ai_result_panel').show();
        $('#ai_result_success').hide();
        $('#ai_result_error').show();
        var msg = 'Request failed';
        if (jqXHR.responseJSON && jqXHR.responseJSON.message) {
            msg = jqXHR.responseJSON.message;
        } else if (jqXHR.statusText) {
            msg += ': ' + jqXHR.statusText;
        }
        $('#ai_result_error_msg').text(msg);
        $('#btn_run_ai_analysis').prop('disabled', false);
    });
}

/* ------------------------------------------------------------------ */
/*  Display result                                                    */
/* ------------------------------------------------------------------ */
function _showResult(resp) {
    $('#ai_progress_panel').hide();
    $('#ai_result_panel').show();

    if (resp.status === 'error') {
        $('#ai_result_success').hide();
        $('#ai_result_error').show();
        $('#ai_result_error_msg').text(resp.error || 'Unknown error');
        $('#btn_run_ai_analysis').prop('disabled', false);
        return;
    }

    $('#ai_result_error').hide();
    $('#ai_result_success').show();
    $('#btn_run_ai_analysis').hide();

    $('#ai_result_summary').text(resp.summary || 'Analysis completed.');

    var risk = resp.risk_level || '-';
    var score = (resp.risk_score != null) ? resp.risk_score + '/100' : '';
    $('#ai_result_risk').text(risk + (score ? ' (' + score + ')' : ''));

    var dur = resp.duration_seconds;
    if (dur != null) {
        var m = Math.floor(dur / 60);
        var s = Math.round(dur % 60);
        $('#ai_result_duration').text(m + 'm ' + s + 's');
    } else {
        $('#ai_result_duration').text('-');
    }

    var usage = resp.usage || {};
    $('#ai_result_input_tokens').text(
        (usage.input_tokens != null) ? usage.input_tokens.toLocaleString() : '-'
    );
    $('#ai_result_output_tokens').text(
        (usage.output_tokens != null) ? usage.output_tokens.toLocaleString() : '-'
    );
    $('#ai_result_tool_calls').text(
        (usage.tool_calls != null) ? usage.tool_calls : '-'
    );
}

/* ------------------------------------------------------------------ */
/*  Elapsed-time ticker                                               */
/* ------------------------------------------------------------------ */
function _startElapsedTimer() {
    _elapsedStart = Date.now();
    $('#ai_elapsed_timer').text('0:00');
    _elapsedInterval = setInterval(function () {
        var secs = Math.floor((Date.now() - _elapsedStart) / 1000);
        var m = Math.floor(secs / 60);
        var s = secs % 60;
        $('#ai_elapsed_timer').text(m + ':' + (s < 10 ? '0' : '') + s);
    }, 1000);
}

function _stopElapsedTimer() {
    if (_elapsedInterval) {
        clearInterval(_elapsedInterval);
        _elapsedInterval = null;
    }
}
