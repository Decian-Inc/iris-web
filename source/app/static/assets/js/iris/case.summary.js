var session_id = null ;
var collaborator = null ;
var buffer_dumped = false ;
var last_applied_change = null ;
var just_cleared_buffer = null ;
var from_sync = null;

var editor = ace.edit("editor_summary",
    {
    autoScrollEditorIntoView: true,
    minLines: 4
    });

var textarea = $('#case_summary');

function Collaborator( session_id ) {
    this.collaboration_socket = io.connect() ;

    this.channel = "case-" + session_id;
    this.collaboration_socket.emit('join', { 'channel': this.channel });

    this.collaboration_socket.on( "change", function(data) {
        delta = JSON.parse( data.delta ) ;
        console.log(delta);
        last_applied_change = delta ;
        $("#content_typing").text(data.last_change + " is typing..");
        editor.getSession().getDocument().applyDeltas( [delta] ) ;
    }.bind() ) ;

    this.collaboration_socket.on( "clear_buffer", function() {
        just_cleared_buffer = true ;
        console.log( "setting editor empty" ) ;
        editor.setValue( "" ) ;
    }.bind() ) ;

    this.collaboration_socket.on( "save", function(data) {
        $("#content_last_saved_by").text("Last saved by " + data.last_saved);
         sync_editor(true);
    }.bind() ) ;
}

Collaborator.prototype.change = function( delta ) {
    this.collaboration_socket.emit( "change", { 'delta': delta, 'channel': this.channel } ) ;
}

Collaborator.prototype.clear_buffer = function() {
    this.collaboration_socket.emit( "clear_buffer", { 'channel': this.channel } ) ;
}

Collaborator.prototype.save = function() {
    this.collaboration_socket.emit( "save", { 'channel': this.channel } ) ;
}

function body_loaded() {

    collaborator = new Collaborator( get_caseid() ) ;

    // registering change callback
    from_sync = true;
    editor.on( "change", function( e ) {
        // TODO, we could make things more efficient and not likely to conflict by keeping track of change IDs
        if( last_applied_change!=e && editor.curOp && editor.curOp.command.name) {
            collaborator.change( JSON.stringify(e) ) ;
        }
    }, false );

    editor.$blockScrolling = Infinity ;

    document.getElementsByTagName('textarea')[0].focus() ;
    last_applied_change = null ;
    just_cleared_buffer = false ;
}

function handle_ed_paste(event) {
    filename = null;
    const { items } = event.originalEvent.clipboardData;
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];

      if (item.kind === 'string') {
        item.getAsString(function (s){
            filename = $.trim(s.replace(/\t|\n|\r/g, '')).substring(0, 40);
        });
      }

      if (item.kind === 'file') {
        const blob = item.getAsFile();

        if (blob !== null) {
            const reader = new FileReader();
            reader.onload = (e) => {
                notify_success('The file is uploading in background. Don\'t leave the page');

                if (filename === null) {
                    filename = random_filename(25);
                }

                upload_interactive_data(e.target.result, filename, function(data){
                    url = data.data.file_url + case_param();
                    event.preventDefault();
                    editor.insertSnippet(`\n![${filename}](${url} =40%x40%)\n`);
                });

            };
            reader.readAsDataURL(blob);
        } else {
            notify_error('Unsupported direct paste of this item. Use datastore to upload.');
        }
      }
    }
}

function report_template_selector() {
    $('#modal_select_report').modal({ show: true });
}

function gen_report(safe) {
    url = '/case/report/generate-investigation/' + $("#select_report option:selected").val() + case_param();
    if (safe === true) {
        url += '&safe=true';
    }
    window.open(url, '_blank');
}

function gen_act_report(safe) {
    url = '/case/report/generate-activities/' + $("#select_report_act option:selected").val() + case_param();
    if (safe === true) {
        url += '&safe=true';
    }
    window.open(url, '_blank');
}

function act_report_template_selector() {
    $('#modal_select_report_act').modal({ show: true });
}

function edit_case_summary() {
    $('#container_editor_summary').toggle();
    if ($('#container_editor_summary').is(':visible')) {
        $('#ctrd_casesum').removeClass('col-md-12').addClass('col-md-6');
        $('#summary_edition_btn').show(100);
        $("#sum_refresh_btn").html('Save');
        $("#sum_edit_btn").html('Close editor');
    } else {
        $('#ctrd_casesum').removeClass('col-md-6').addClass('col-md-12');
        $('#summary_edition_btn').hide();
        $("#sum_refresh_btn").html('Refresh');
        $("#sum_edit_btn").html('Edit');
    }
}

/* sync_editor
* Save the editor state.
* Check if there are external changes first.
* Copy local changes if conflict
*/
function sync_editor(no_check) {

    $('#last_saved').text('Syncing..').addClass('badge-danger').removeClass('badge-success');

    get_request_api('/case/summary/fetch')
    .done((data) => {
        if (data.status == 'success') {
            if (no_check) {
                // Set the content from remote server
                from_sync = true;
                editor.getSession().setValue(data.data.case_description);

                // Set the CRC in page
                $('#fetched_crc').val(data.data.crc32.toString());
                $('#last_saved').text('Changes saved').removeClass('badge-danger').addClass('badge-success');
                $('#content_last_sync').text("Last synced: " + new Date().toLocaleTimeString());
            }
            else {
                // Check if content is different
                st = editor.getSession().getValue();
                if (data.data.crc32 != $('#fetched_crc').val()) {
                    // Content has changed remotely
                    // Check if we have changes locally
                    local_crc = crc32(st).toString();
                    console.log('Content changed. Local CRC is ' + local_crc);
                    console.log('Saved CRC is ' + $('#fetched_crc').val());
                    console.log('Remote CRC is ' + data.data.crc32);
                    if (local_crc == $('#fetched_crc').val()) {
                        // No local change, we can sync and update local CRC
                        editor.getSession().setValue(data.data.case_description);
                        $('#fetched_crc').val(data.data.crc32);
                        $('#last_saved').text('Changes saved').removeClass('badge-danger').addClass('badge-success');
                        $('#content_last_sync').text("Last synced: " + new Date().toLocaleTimeString());
                    } else {
                        // We have a conflict
                        $('#last_saved').text('Conflict !').addClass('badge-danger').removeClass('badge-success');
                        swal ( "Oh no !" ,
                        "We have a conflict with the remote content.\nSomeone may just have changed the description at the same time.\nThe local content will be copied into clipboard and content will be updated with remote." ,
                        "error"
                        ).then((value) => {
                            // Old fashion trick
                            editor.selectAll();
                            editor.focus();
                            document.execCommand('copy');
                            editor.getSession().setValue(data.data.desc);
                            $('#fetched_crc').val(data.data.crc32);
                            notify_success('Content updated with remote. Local changes copied to clipboard.');
                            $('#content_last_sync').text("Last synced: " + new Date().toLocaleTimeString());
                        });
                    }
                } else {
                    // Content did not change remotely
                    // Check local change
                    local_crc = crc32(st).toString();
                    if (local_crc != $('#fetched_crc').val()) {
                        console.log('Local change. Old CRC is ' + local_crc);
                        console.log('New CRC is ' + $('#fetched_crc').val());
                        var data = Object();
                        data['case_description'] = st;
                        data['csrf_token'] = $('#csrf_token').val();
                        // Local change detected. Update to remote
                        $.ajax({
                            url: '/case/summary/update' + case_param(),
                            type: "POST",
                            dataType: "json",
                            contentType: "application/json;charset=UTF-8",
                            data: JSON.stringify(data),
                            success: function (data) {
                                if (data.status == 'success') {
                                    collaborator.save();
                                    $('#content_last_sync').text("Last synced: " + new Date().toLocaleTimeString());
                                    $('#fetched_crc').val(data.data);
                                    $('#last_saved').text('Changes saved').removeClass('badge-danger').addClass('badge-success');
                                } else {
                                    notify_error("Unable to save content to remote server");
                                    $('#last_saved').text('Error saving !').addClass('badge-danger').removeClass('badge-success');
                                }
                            },
                            error: function(error) {
                                notify_error(error.responseJSON.message);
                                ('#last_saved').text('Error saving !').addClass('badge-danger').removeClass('badge-success');
                            }
                        });
                    }
                    $('#content_last_sync').text("Last synced: " + new Date().toLocaleTimeString());
                    $('#last_saved').text('Changes saved').removeClass('badge-danger').addClass('badge-success');
                }
            }
        }
    });
}


is_typing = "";
function auto_remove_typing() {
    if ($("#content_typing").text() == is_typing) {
        $("#content_typing").text("");
    } else {
        is_typing = $("#content_typing").text();
    }
}

function case_pipeline_popup() {
    url = '/case/pipelines-modal' + case_param();
    $('#info_case_modal_content').load(url, function (response, status, xhr) {
        if (status !== "success") {
             ajax_notify_error(xhr, url);
             return false;
        }
        $('#modal_case_detail').modal({ show: true });
        $("#update_pipeline_selector").selectpicker({
            liveSearch: true,
            style: "btn-outline-white"
            })
        $('#update_pipeline_selector').selectpicker("refresh");
        $(".control-update-pipeline-args ").hide();
        $('.control-update-pipeline-'+ $('#update_pipeline_selector').val() ).show();
        $('#update_pipeline_selector').on('change', function(e){
          $(".control-update-pipeline-args ").hide();
          $('.control-update-pipeline-'+this.value).show();
        });
        $('[data-toggle="popover"]').popover();
    });
}

async function do_case_review(action, reviewer_id) {
    let data = Object();
    data['csrf_token'] = $('#csrf_token').val();
    data['action'] = action;
    if (reviewer_id) {
        data['reviewer_id'] = reviewer_id;
    }

    return post_request_api('/case/review/update', JSON.stringify(data));
}

function case_detail(case_id, edit_mode=false) {
    url = '/case/details/' + case_id + case_param();
    $('#info_case_modal_content').load(url, function (response, status, xhr) {
        if (status !== "success") {
             ajax_notify_error(xhr, url);
             return false;
        }
        $('#modal_case_detail').modal({ show: true });
        if (edit_mode) {
            edit_case_info();
        }

        $('#modal_case_detail').off('hide.bs.modal').on("hide.bs.modal", function (e) {
            location.reload();
        });
    });
}

function manage_case(case_id) {
   window.location = '/manage/cases?cid='+ case_id +'#view';
}


function parse_description_match_context(description) {
    if (!description) return null;

    var markers = ['### Match Context', '--- Match Context ---'];
    var idx = -1;
    var markerLen = 0;
    for (var i = 0; i < markers.length; i++) {
        idx = description.indexOf(markers[i]);
        if (idx !== -1) {
            markerLen = markers[i].length;
            break;
        }
    }
    if (idx === -1) return null;

    var block = description.substring(idx + markerLen);

    var ctx = {};
    var fieldMap = {
        'Wazuh Rule':        function(v) {
            var parts = v.match(/^(\S+)\s*-\s*(.+)/);
            if (parts) { ctx.rule_id = parts[1].trim(); ctx.rule_description = parts[2].trim(); }
            else { ctx.rule_id = v.trim(); }
        },
        'Rule Level':        function(v) { ctx.rule_level = v; },
        'Fired Times':       function(v) { ctx.fired_times = v; },
        'Alert Set':         function(v) { ctx.alert_set = v; },
        'Case Definition':   function(v) { ctx.case_definition = v; },
        'Triggering Agent':  function(v) { ctx.triggering_agent = v.replace(/\s*\(\d+\)\s*$/, ''); },
        'Tenant':            function(v) { ctx.tenant_key = v; },
        'MITRE IDs':         function(v) { ctx.mitre_ids = v; },
        'MITRE Tactics':     function(v) { ctx.mitre_tactics = v; },
        'MITRE Techniques':  function(v) { ctx.mitre_techniques = v; },
        'First Seen':        function(v) { ctx.first_seen = v; }
    };

    for (var label in fieldMap) {
        var mdPattern = new RegExp('\\*\\*' + label + ':\\*\\*\\s*(.+)');
        var plainPattern = new RegExp(label + ':\\s*(.+)');
        var m = block.match(mdPattern) || block.match(plainPattern);
        if (m) {
            fieldMap[label](m[1].trim());
        }
    }

    return Object.keys(ctx).length > 0 ? ctx : null;
}

function open_exception_modal() {
    $('#exception_tenant_key').val('');
    $('#exception_rule_id').val('');
    $('#exception_agent_name').val('');
    $('#exception_case_tags').val('');
    $('#exception_duration_hours').val(168);
    $('#exception_reason').val('');
    $('#exception_created_by').val($('#current_user_login').text().trim());
    $('#exception_match_context_panel').hide();

    $('#ctx_rule_id, #ctx_rule_description, #ctx_triggering_agent').text('');
    $('#ctx_alert_set, #ctx_case_definition').text('');
    $('#ctx_mitre_ids, #ctx_mitre_tactics, #ctx_mitre_techniques').text('');
    $('#ctx_triggered_rule_ids').text('');

    get_request_api('/case/meta')
    .done(function(data) {
        if (data.status === 'success' && data.data) {
            var caseData = data.data;
            var matchCtx = null;

            if (caseData.custom_attributes && caseData.custom_attributes.match_context
                && Object.keys(caseData.custom_attributes.match_context).length > 0) {
                matchCtx = caseData.custom_attributes.match_context;
            }

            if (!matchCtx && caseData.description) {
                matchCtx = parse_description_match_context(caseData.description);
            }

            if (caseData.client && caseData.client.customer_name) {
                $('#exception_tenant_key').val(caseData.client.customer_name);
            }

            if (matchCtx) {
                $('#exception_match_context_panel').show();

                $('#ctx_rule_id').text(matchCtx.rule_id || '—');
                $('#ctx_rule_description').text(matchCtx.rule_description || '');
                $('#ctx_triggering_agent').text(matchCtx.triggering_agent || '—');
                $('#ctx_alert_set').text(matchCtx.alert_set || '—');
                $('#ctx_case_definition').text(matchCtx.case_definition || '—');
                $('#ctx_mitre_ids').text(matchCtx.mitre_ids || '—');
                $('#ctx_mitre_tactics').text(matchCtx.mitre_tactics || '—');
                $('#ctx_mitre_techniques').text(matchCtx.mitre_techniques || '—');

                var ruleIds = matchCtx.triggered_rule_ids || [];
                $('#ctx_triggered_rule_ids').text(ruleIds.length > 0 ? ruleIds.join(', ') : '—');

                if (matchCtx.tenant_key) {
                    $('#exception_tenant_key').val(matchCtx.tenant_key);
                }
                if (ruleIds.length > 0) {
                    $('#exception_rule_id').val(ruleIds.join(', '));
                } else if (matchCtx.rule_id) {
                    $('#exception_rule_id').val(matchCtx.rule_id);
                }
                if (matchCtx.triggering_agent) {
                    $('#exception_agent_name').val(matchCtx.triggering_agent);
                }
            }

            if (caseData.tags && caseData.tags.length > 0) {
                var tagStr = caseData.tags.map(function(t) { return t.tag_title; }).join(', ');
                $('#exception_case_tags').val(tagStr);
            }
        }
        $('#modal_create_exception').modal({ show: true });
    })
    .fail(function() {
        $('#modal_create_exception').modal({ show: true });
    });
}

function submit_exception() {
    var tenantKey = $('#exception_tenant_key').val().trim();
    var ruleId = $('#exception_rule_id').val().trim();
    var agentName = $('#exception_agent_name').val().trim();
    var caseTags = $('#exception_case_tags').val().trim();
    var durationHours = parseInt($('#exception_duration_hours').val(), 10);
    var reason = $('#exception_reason').val().trim();
    var createdBy = $('#exception_created_by').val().trim();

    if (!tenantKey) {
        notify_error('Tenant Key is required');
        return;
    }

    if (!ruleId && !agentName && !caseTags) {
        notify_error('At least one criteria field (Rule ID, Agent Name, or Case Tags) is required');
        return;
    }

    var criteria = {};
    if (ruleId) {
        var ruleIdParts = ruleId.split(',').map(function(r) { return r.trim(); }).filter(function(r) { return r !== ''; });
        criteria.rule_id = ruleIdParts.length === 1 ? ruleIdParts[0] : ruleIdParts;
    }
    if (agentName) {
        criteria.agent_name = agentName;
    }
    if (caseTags) {
        criteria.case_tags = caseTags.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t !== ''; });
    }

    var payload = {
        tenant_key: tenantKey,
        criteria: criteria,
        csrf_token: $('#csrf_token').val()
    };

    if (durationHours && durationHours > 0) {
        payload.duration_hours = durationHours;
    }
    if (reason) {
        payload.reason = reason;
    }
    if (createdBy) {
        payload.created_by = createdBy;
    }

    $('#submit_exception').prop('disabled', true).html('<i class="fa-solid fa-spinner fa-spin mr-1"></i> Creating...');

    post_request_api('/case/exceptions/create', JSON.stringify(payload))
    .done(function(data) {
        if (notify_auto_api(data)) {
            $('#modal_create_exception').modal('hide');
        }
    })
    .always(function() {
        $('#submit_exception').prop('disabled', false).html('<i class="fa-solid fa-check mr-1"></i> Create Exception');
    });
}

$(document).ready(function() {

    if ($("#editor_summary").attr("data-theme") !== "dark") {
        editor.setTheme("ace/theme/tomorrow");
    } else {
        editor.setTheme("ace/theme/iris_night");
    }
    editor.session.setMode("ace/mode/markdown");
    editor.renderer.setShowGutter(true);
    editor.setOption("showLineNumbers", true);
    editor.setOption("showPrintMargin", false);
    editor.setOption("displayIndentGuides", true);
    editor.setOption("indentedSoftWrap", false);
    editor.session.setUseWrapMode(true);
    editor.setOption("maxLines", "Infinity")
    editor.renderer.setScrollMargin(8, 5)
    editor.setOption("enableBasicAutocompletion", true);
    editor.commands.addCommand({
        name: 'save',
        bindKey: {win: "Ctrl-S", "mac": "Cmd-S"},
        exec: function(editor) {
            sync_editor(false);
        }
    })
    editor.commands.addCommand({
        name: 'bold',
        bindKey: {win: "Ctrl-B", "mac": "Cmd-B"},
        exec: function(editor) {
            editor.insertSnippet('**${1:$SELECTION}**');
        }
    });
    editor.commands.addCommand({
        name: 'italic',
        bindKey: {win: "Ctrl-I", "mac": "Cmd-I"},
        exec: function(editor) {
            editor.insertSnippet('*${1:$SELECTION}*');
        }
    });
    editor.commands.addCommand({
        name: 'head_1',
        bindKey: {win: "Ctrl-Shift-1", "mac": "Cmd-Shift-1"},
        exec: function(editor) {
            editor.insertSnippet('# ${1:$SELECTION}');
        }
    });
    editor.commands.addCommand({
        name: 'head_2',
        bindKey: {win: "Ctrl-Shift-2", "mac": "Cmd-Shift-2"},
        exec: function(editor) {
            editor.insertSnippet('## ${1:$SELECTION}');
        }
    });
    editor.commands.addCommand({
        name: 'head_3',
        bindKey: {win: "Ctrl-Shift-3", "mac": "Cmd-Shift-3"},
        exec: function(editor) {
            editor.insertSnippet('### ${1:$SELECTION}');
        }
    });
    editor.commands.addCommand({
        name: 'head_4',
        bindKey: {win: "Ctrl-Shift-4", "mac": "Cmd-Shift-4"},
        exec: function(editor) {
            editor.insertSnippet('#### ${1:$SELECTION}');
        }
    });
    $('#editor_summary').on('paste', (event) => {
        event.preventDefault();
        handle_ed_paste(event);
    });

    var timer;
    var timeout = 10000;
    $('#editor_summary').keyup(function(){
        if(timer) {
             clearTimeout(timer);
        }
        timer = setTimeout(sync_editor, timeout);
    });


    //var textarea = $('#case_summary');
    editor.getSession().on("change", function () {
        //textarea.val(do_md_filter_xss(editor.getSession().getValue()));
        $('#last_saved').text('Changes not saved').addClass('badge-danger').removeClass('badge-success');
        let target = document.getElementById('targetDiv');
        let converter = get_showdown_convert();
        let html = converter.makeHtml(do_md_filter_xss(editor.getSession().getValue()));

        target.innerHTML = do_md_filter_xss(html);

    });

    edit_case_summary();
    body_loaded();
    sync_editor(true);
    setInterval(auto_remove_typing, 2000);

    let review_state = $('#caseReviewState');
    if (review_state.length > 0) {
        let current_review_state = review_state.data('review-state');

        if (current_review_state === 'Review in progress') {
            $(".btn-start-review").hide();
            $(".btn-confirm-review").show();
            $(".btn-cancel-review").show();
            $('#reviewSubtitle').text('You started this review. Press "Confirm review" when you are done.');
        } else if (current_review_state === 'Review completed') {
            $(".btn-start-review").hide();
            $(".btn-confirm-review").hide();
            $(".btn-cancel-review").hide();
        } else if (current_review_state === 'Pending review') {
            $(".btn-start-review").show();
            $(".btn-confirm-review").hide();
            $(".btn-cancel-review").hide();
        }
        $('.review-card').show();
    }

    $('.btn-start-review').on('click', function(e){
        do_case_review('start').then(function(data) {
            if (notify_auto_api(data)) {
                location.reload();
            }
        });
    });

     $('.btn-confirm-review').on('click', function(e){
        do_case_review('done').then(function(data) {
            if (notify_auto_api(data)) {
                location.reload();
            }
        });
     });

     $('.btn-cancel-review').on('click', function(e){
        do_case_review('cancel').then(function(data) {
            if (notify_auto_api(data)) {
                location.reload();
            }
        });
     });

     $('#request_review').on('click', function(e){
        let reviewer_id = $('#caseReviewState').data('reviewer-id');
        let reviewer_name = $('#caseReviewState').data('reviewer-name');



        if (reviewer_id !== "None") {
            swal({
                title: "Request review",
                text: "Request a case review from " + reviewer_name + "?",
                icon: "info",
                buttons: true,
                dangerMode: false,
            }).then((willRequest) => {
                if (willRequest) {
                    do_case_review('request', reviewer_id).then(function (data) {
                        if (notify_auto_api(data)) {
                            location.reload();
                        }
                    });
                }
            });
        } else {
            $('#reviewer_id').selectpicker({
                liveSearch: true,
                size: 10,
                width: '100%'
            });
            get_request_api('/case/users/list')
            .done((data) => {
                if (notify_auto_api(data)) {
                    let users = data.data;
                    let options = '';
                    for (let i = 0; i < users.length; i++) {
                        if (users[i].user_access_level === 4) {
                            options += '<option value="' + users[i].user_id + '">' + filterXSS(users[i].user_name) + '</option>';
                        }
                    }
                    $('#reviewer_id').html(options);
                    $('#reviewer_id').selectpicker('refresh');
                    $('#modal_choose_reviewer').modal('show');

                    $('#submit_set_reviewer').off('click').on('click', function(e){
                        let reviewer_id = $('#reviewer_id').val();
                        do_case_review('request', reviewer_id).then(function (data) {
                            if (notify_auto_api(data)) {
                                location.reload();
                            }
                        });
                    });
                }
            });

        }

     });

});


