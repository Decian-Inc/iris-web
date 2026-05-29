# Implementation Guide: Per-Customer Wazuh Callback URL

## Overview

The postprocessor's `DataPreparer._build_wazuh_case_link()` builds a full Wazuh URL and embeds it as a raw `<a>` tag inside the case description markdown:

```
https://wazuh.ironclad.{environment}/app/data-explorer/discover#?_a=...&_q=(filters:!(rule.id=X,agent.name=Y,...))
```

The full path and query string are alert-specific (rule ID, agent, tenant filters). Only the **origin** changes per customer — i.e. `wazuh` → `blackbirch`, or `ironclad.decianx` → `ironclad.ofdecian.com`.

The strategy is:
1. Store a `callback_url` base (e.g. `https://blackbirch.ironclad.ofdecian.com`) per `Client` record in IRIS.
2. Expose it through the existing `/case/meta` API, which already nests the full `CustomerSchema` under `data.client`.
3. In `case.summary.js`, after every render of the case description into `targetDiv`, scan for `<a>` elements whose text is `"View in Wazuh"` and swap only the origin of their `href` with the customer's `callback_url`. Everything after the origin (path, query string, hash) is preserved.
4. Expose the field in the customer admin UI (view page + edit modal), gated by the existing `customers_write` permission — no new permission needed.

The postprocessor does **not** need to change. Old cases and new cases are both handled transparently at render time.

---

## Files to Change

| # | File | What changes |
|---|------|--------------|
| 1 | `source/app/models/models.py` | Add `callback_url` column to `Client` |
| 2 | `source/app/alembic/versions/<new>.py` | Migration to add the column |
| 3 | `source/app/schema/marshables.py` | Expose `customer_callback_url` in `CustomerSchema` |
| 4 | `source/app/datamgmt/client/client_db.py` | Include `callback_url` in `get_client_api()` and `get_client_list()` queries |
| 5 | `source/app/forms.py` | Add `customer_callback_url` field to `AddCustomerForm` |
| 6 | `source/app/blueprints/manage/manage_customers_routes.py` | Populate the new field in `view_customer_modal` |
| 7 | `source/app/blueprints/manage/templates/modal_add_customer.html` | Add URL input to edit modal |
| 8 | `source/app/blueprints/manage/templates/manage_customer_view.html` | Add "Call Back URL" collapsible section |
| 9 | `source/app/static/assets/js/iris/case.summary.js` | Fetch callback URL and replace link origins after render |

`view.customers.js` and `manage.customers.js` require **no changes** — the edit modal already uses `$('#form_new_customer').serializeObject()` to collect all form fields before posting, so the new input field is picked up automatically.

---

## Change 1 — `source/app/models/models.py`

### Location
`Client` class, lines 130–142.

### Current
```python
class Client(db.Model):
    __tablename__ = 'client'

    client_id = Column(BigInteger, primary_key=True)
    client_uuid = Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"), nullable=False)
    name = Column(Text, unique=True)
    description = Column(Text)
    sla = Column(Text)
    creation_date = Column(DateTime, server_default=func.now(), nullable=True)
    created_by = Column(ForeignKey('user.id'), nullable=True)
    last_update_date = Column(DateTime, server_default=func.now(), nullable=True)
    custom_attributes = Column(JSON)
```

### Change
Add one line after `sla`:
```python
    sla = Column(Text)
    callback_url = Column(Text, nullable=True)   # ADD THIS LINE
```

---

## Change 2 — New Alembic Migration

### How migrations work in this project

- Migrations are **written by hand** — there is no autogenerate (`target_metadata = None` in `env.py`).
- They live in `source/app/alembic/versions/` and are run automatically at startup via `post_init.py` which calls `command.upgrade(alembic_cfg, 'head')`.
- Do **not** run `alembic revision` to generate the file. Create it manually.

### Current HEAD

The revision chain ends at `0d65689ff498`. The full tail of the DAG:

```
0d65689ff496
  ├─→ 3ed7b2369672 → 4f5c6d7e8a9b → 5g6h7i8j9k0l → 6h7i8j9k0l1m ─┐
  └─────────────────────────────────────────────────────────────────┘
                                                               0d65689ff497  (merge)
                                                                    ↓
                                                               0d65689ff498  ← HEAD
```

The new migration must have `down_revision = '0d65689ff498'`.

### Guard pattern

Older migrations used `_table_has_column` from `alembic_utils.py`. Every migration from `3ed7b2369672` onward uses `sa.inspect(conn)` directly. Use the newer pattern.

### Complete file

Create: `source/app/alembic/versions/a1b2c3d4e5f6_add_callback_url_to_client.py`

```python
"""Add callback_url to client table

Revision ID: a1b2c3d4e5f6
Revises: 0d65689ff498
Create Date: 2026-05-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '0d65689ff498'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_columns = [col['name'] for col in inspector.get_columns('client')]
    if 'callback_url' not in existing_columns:
        op.add_column('client', sa.Column('callback_url', sa.Text(), nullable=True))


def downgrade():
    pass
```

The `existing_columns` guard means re-running the migration (e.g. on a DB that already has the column) is safe and idempotent.

---

## Change 3 — `source/app/schema/marshables.py`

### Location
`CustomerSchema`, lines 1710–1726.

### Current field declarations + Meta
```python
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    customer_name: str = auto_field('name', required=True, validate=Length(min=2), allow_none=False)
    customer_description: Optional[str] = auto_field('description', allow_none=True)
    customer_sla: Optional[str] = auto_field('sla', allow_none=True)
    customer_id: int = auto_field('client_id')

    class Meta:
        model = Client
        load_instance = True
        exclude = ['name', 'client_id', 'description', 'sla']
        unknown = EXCLUDE
```

### Change
Add one field declaration after `customer_sla`, and add `'callback_url'` to the `Meta.exclude` list (so the raw column name is not double-serialized alongside the aliased field):

```python
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    customer_name: str = auto_field('name', required=True, validate=Length(min=2), allow_none=False)
    customer_description: Optional[str] = auto_field('description', allow_none=True)
    customer_sla: Optional[str] = auto_field('sla', allow_none=True)
    customer_callback_url: Optional[str] = auto_field('callback_url', allow_none=True)  # ADD
    customer_id: int = auto_field('client_id')

    class Meta:
        model = Client
        load_instance = True
        exclude = ['name', 'client_id', 'description', 'sla', 'callback_url']  # ADD 'callback_url'
        unknown = EXCLUDE
```

### Why this matters for the case view
`CaseDetailsSchema` (line 2350) nests `CustomerSchema` directly:
```python
client = ma.Nested(CustomerSchema)
```
So the `/case/meta` endpoint automatically returns `data.client.customer_callback_url` once the schema field is added — no route changes needed.

---

## Change 4 — `source/app/datamgmt/client/client_db.py`

Two query functions need the new column added.

### `get_client_list()` — lines 43–52

#### Current
```python
    client_list = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id'),
        Client.client_uuid.label('customer_uuid'),
        Client.description.label('customer_description'),
        Client.sla.label('customer_sla'),
        Client.custom_attributes
    ).filter(filter).all()
```

#### Change — add one line
```python
    client_list = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id'),
        Client.client_uuid.label('customer_uuid'),
        Client.description.label('customer_description'),
        Client.sla.label('customer_sla'),
        Client.callback_url.label('customer_callback_url'),   # ADD
        Client.custom_attributes
    ).filter(filter).all()
```

### `get_client_api()` — lines 65–72

#### Current
```python
    client = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id'),
        Client.client_uuid.label('customer_uuid'),
        Client.description.label('customer_description'),
        Client.sla.label('customer_sla'),
        Client.custom_attributes
    ).filter(Client.client_id == client_id).first()
```

#### Change — add one line
```python
    client = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id'),
        Client.client_uuid.label('customer_uuid'),
        Client.description.label('customer_description'),
        Client.sla.label('customer_sla'),
        Client.callback_url.label('customer_callback_url'),   # ADD
        Client.custom_attributes
    ).filter(Client.client_id == client_id).first()
```

`get_client_api()` is what `view_customer_page` uses to pass `customer` to the template, and what `view_customer` uses for the `GET /manage/customers/<id>` API. Both will automatically expose the new field once it's in the query.

---

## Change 5 — `source/app/forms.py`

### Location
`AddCustomerForm`, lines 57–60.

### Current
```python
class AddCustomerForm(FlaskForm):
    customer_name = StringField(u'Customer name', validators=[DataRequired()])
    customer_description = TextAreaField(u'Customer description', validators=[DataRequired()])
    customer_sla = TextAreaField(u'Customer SLAs', validators=[DataRequired()])
```

### Change
```python
class AddCustomerForm(FlaskForm):
    customer_name = StringField(u'Customer name', validators=[DataRequired()])
    customer_description = TextAreaField(u'Customer description', validators=[DataRequired()])
    customer_sla = TextAreaField(u'Customer SLAs', validators=[DataRequired()])
    customer_callback_url = StringField(u'Callback URL')   # ADD — no DataRequired, it's optional
```

---

## Change 6 — `source/app/blueprints/manage/manage_customers_routes.py`

### Location
`view_customer_modal`, lines 306–323. This route loads the edit modal for an existing customer. It manually populates form fields via `render_kw`.

### Current
```python
    form.customer_name.render_kw = {'value': customer.name}
    form.customer_description.data = customer.description
    form.customer_sla.data = customer.sla

    return render_template("modal_add_customer.html", form=form, customer=customer,
                           attributes=customer.custom_attributes)
```

### Change — add one line before the return
```python
    form.customer_name.render_kw = {'value': customer.name}
    form.customer_description.data = customer.description
    form.customer_sla.data = customer.sla
    form.customer_callback_url.render_kw = {'value': customer.callback_url or ''}   # ADD

    return render_template("modal_add_customer.html", form=form, customer=customer,
                           attributes=customer.custom_attributes)
```

Note: `customer` here is the raw `Client` ORM object (from `get_client()`, not `get_client_api()`), so `.callback_url` is the direct column attribute. The `or ''` guard handles NULL safely.

---

## Change 7 — `source/app/blueprints/manage/templates/modal_add_customer.html`

### Location
Inside the `<form id="form_new_customer">` block, after the SLAs group (currently line 37).

### Current — the SLAs group block
```html
                                <div class="form-group">
                                    <label for="sla" class="mr-4">SLAs</label>
                                    {{ form.customer_sla(class='form-control',  autocomplete="off") }}
                                </div>
```

### Change — add a new form-group immediately after it
```html
                                <div class="form-group">
                                    <label for="sla" class="mr-4">SLAs</label>
                                    {{ form.customer_sla(class='form-control',  autocomplete="off") }}
                                </div>
                                <div class="form-group">
                                    <label for="customer_callback_url" class="mr-4">Callback URL</label>
                                    {{ form.customer_callback_url(class='form-control', autocomplete="off", placeholder="https://wazuh.ironclad.decianx") }}
                                    <small class="form-text text-muted">Base URL of this customer's Wazuh instance. Overrides the default origin in "View in Wazuh" links.</small>
                                </div>
```

The placeholder shows the default value so it's clear what format is expected when left blank.

---

## Change 8 — `source/app/blueprints/manage/templates/manage_customer_view.html`

### Location
After the Assets collapsible card (which ends at line 346), before the closing `</div>` of the main content area at line 348.

### Current structure around that area
```html
               </div>   ← closes Assets card-body
            </div>      ← closes Assets card
          </div>        ← closes Assets row

        </div>          ← closes page-inner main content
    {% endif %}
```

### Change — insert a new card row between Assets and the closing `</div>`

```html
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <div class="row">
                                    <div class="col-12">
                                        <div class="row">
                                            <div class="col col-heading collapsed" href="#collapse_client_callback_view" title="Click to unfold" data-toggle="collapse" role="button" aria-expanded="false" aria-controls="collapse_client_callback_view">
                                                <span class="accicon float-left mr-3"><i class="fas fa-angle-right rotate-icon"></i></span>
                                                <div class="card-title">Call Back URL</div>
                                            </div>
                                            <div class="col">
                                                <button class="btn btn-light btn-sm float-right" onclick="customer_detail('{{ customer.customer_id }}');">Edit</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-body collapse" id="collapse_client_callback_view">
                                {% if customer.customer_callback_url %}
                                    <p class="mb-1"><strong>Configured URL:</strong></p>
                                    <code>{{ customer.customer_callback_url }}</code>
                                    <p class="mt-2 text-muted">This base URL replaces the default Wazuh origin in "View in Wazuh" links for cases belonging to this customer.</p>
                                {% else %}
                                    <p class="text-muted">No callback URL configured. The default Wazuh URL will be used.</p>
                                    <button class="btn btn-light btn-sm mt-1" onclick="customer_detail('{{ customer.customer_id }}');">Configure</button>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
```

**Why "Edit" calls `customer_detail()`:** `customer_detail()` in `manage.customers.js` opens the same edit modal (`modal_add_customer.html`) that already has the Callback URL field after Change 7. No new modal or route is needed.

**Access control:** The section is visible to anyone with `customers_read`. Editing requires `customers_write` (enforced server-side at `POST /manage/customers/update/<id>`). The Edit/Configure buttons open the modal — if the user lacks write permission the server will reject the POST. This mirrors how all other customer fields work.

---

## Change 9 — `source/app/static/assets/js/iris/case.summary.js`

This is the key runtime wire-up. Two additions are needed.

### 9a — Module-level variable and helper function

Add near the top of the file, after the existing `var` declarations (after line 6):

```javascript
var _customer_callback_url = null;

function _apply_wazuh_callback(target) {
    if (!_customer_callback_url) { return; }
    $(target).find('a').each(function () {
        var text = $(this).text().trim();
        if (text === 'View in Wazuh' || text === 'View Message in Wazuh') {
            var href = $(this).attr('href');
            if (!href) { return; }
            try {
                var url = new URL(href);
                var cb  = new URL(_customer_callback_url);
                url.protocol = cb.protocol;
                url.host     = cb.host;
                $(this).attr('href', url.toString());
            } catch (e) { /* malformed URL — leave unchanged */ }
        }
    });
}
```

**What it does:** For each anchor whose visible text is exactly `"View in Wazuh"` or `"View Message in Wazuh"` (the second text appears in timeline event entries from `prepare_event_data`), it replaces only the `protocol` and `host` of the `href` with those from `_customer_callback_url`. The rest of the URL — `/app/data-explorer/discover#?_a=...&_q=(filters:!(rule.id=X,...))` — is untouched, so the alert-specific filters the postprocessor built still work.

### 9b — Hook into the editor change event

The editor's change listener is at lines 580–589. The `target.innerHTML` assignment is what puts the rendered HTML into the page.

#### Current
```javascript
    editor.getSession().on("change", function () {
        $('#last_saved').text('Changes not saved').addClass('badge-danger').removeClass('badge-success');
        let target = document.getElementById('targetDiv');
        let converter = get_showdown_convert();
        let html = converter.makeHtml(do_md_filter_xss(editor.getSession().getValue()));
        target.innerHTML = do_md_filter_xss(html);
    });
```

#### Change — add one call after `target.innerHTML`
```javascript
    editor.getSession().on("change", function () {
        $('#last_saved').text('Changes not saved').addClass('badge-danger').removeClass('badge-success');
        let target = document.getElementById('targetDiv');
        let converter = get_showdown_convert();
        let html = converter.makeHtml(do_md_filter_xss(editor.getSession().getValue()));
        target.innerHTML = do_md_filter_xss(html);
        _apply_wazuh_callback(target);   // ADD
    });
```

### 9c — Fetch the callback URL on document ready and apply retroactively

The `$(document).ready` block (line 498) ends after the interval and review state setup. `sync_editor(true)` is called at line 593, which triggers the change event — but `_customer_callback_url` is still `null` at that point because the `/case/meta` fetch hasn't resolved yet.

The fix is: fetch `/case/meta` on ready, store the URL, then immediately apply it to whatever is already in `targetDiv`.

Add this block inside `$(document).ready`, after the `sync_editor(true)` call at line 593:

```javascript
    get_request_api('/case/meta')
    .done(function (data) {
        if (data.status === 'success' && data.data && data.data.client) {
            var cb = data.data.client.customer_callback_url;
            if (cb) {
                _customer_callback_url = cb;
                _apply_wazuh_callback(document.getElementById('targetDiv'));
            }
        }
    });
```

**Timing rationale:**
- `sync_editor(true)` fires, fetches the description, sets the editor, triggers the change event, sets `targetDiv.innerHTML` — all before the `/case/meta` call resolves.
- When `/case/meta` resolves, `_customer_callback_url` is set and `_apply_wazuh_callback` is called on the already-populated `targetDiv` to fix up the links retroactively.
- For any subsequent editor changes (e.g. if the user edits the description), `_customer_callback_url` is now populated so the change handler's `_apply_wazuh_callback(target)` call works immediately.

---

## Data Flow Summary

```
Admin sets callback_url in customer edit modal
  → POST /manage/customers/update/<id>
  → update_client() → CustomerSchema.load() → writes Client.callback_url to DB

User opens a case
  → case.summary.js: sync_editor(true) → /case/summary/fetch → renders description → targetDiv.innerHTML set
  → case.summary.js: GET /case/meta → CaseDetailsSchema → nested CustomerSchema
      → data.client.customer_callback_url = "https://blackbirch.ironclad.ofdecian.com"
  → _apply_wazuh_callback(targetDiv):
      finds <a>View in Wazuh</a>
      href was: https://wazuh.ironclad.decianx/app/data-explorer/discover#?...filters...
      href now: https://blackbirch.ironclad.ofdecian.com/app/data-explorer/discover#?...same filters...
```

---

## What Does NOT Need to Change

- **`view.customers.js`** — `serializeObject()` on the form automatically includes `customer_callback_url` in the POST body. The save path is already wired.
- **`manage.customers.js`** — `customer_detail()` already opens the modal and submits to the correct endpoint.
- **`case_routes.py`** — `/case/meta` already returns the nested client. Once `CustomerSchema` includes the field, it flows through with zero route changes.
- **The postprocessor** — continues to build URLs exactly as before. IRIS rewrites the origin at render time.
- **Permissions** — `customers_write` already guards all mutation routes. No new permission required.
