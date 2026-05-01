● The exploration gives me everything I need. Here's the full implementation plan:
                                                                                                                                                 
  ---
  Implementation Plan: Customer-Based Case Access Control                                                                                        
                  
  What Already Exists (Don't Rebuild)                                                                                                            
                  
  The infrastructure is almost entirely in place. The key chain is:

  UserClient (user → customer assignment)
      ↓ via ac_auto_update_user_effective_access()
  UserCaseEffectiveAccess (user → case, computed)
      ↓ via user_list_cases_view()
  get_filtered_cases() → case list API

  ┌──────────────────────────────────────────────────┬──────────────────────────────────┬────────┐
  │                    Component                     │               File               │ Status │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ User-customer join table (UserClient)            │ authorization.py:167             │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ Effective access table (UserCaseEffectiveAccess) │ authorization.py:126             │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ Customer assignment UI modal                     │ modal_manage_user_customers.html │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ Customer assignment POST route                   │ manage_users.py:267              │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ update_user_customers() with recompute call      │ manage_users_db.py:153           │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ Case filter using effective access               │ manage_cases_db.py:469           │ Exists │
  ├──────────────────────────────────────────────────┼──────────────────────────────────┼────────┤
  │ New case → grant customer members access         │ access_control/utils.py:407      │ Exists │
  └──────────────────────────────────────────────────┴──────────────────────────────────┴────────┘

  ---
  Phase 1 — Audit & Verify the Existing Pipeline

  Before writing any new code, verify these three things actually wire up end-to-end.

  1a. Confirm ac_set_new_case_access() is called on case creation

  Find where cases are created and confirm the call is there:

  grep -rn "ac_set_new_case_access" source/
  grep -rn "create_case\|add_case\|new_case" source/app/blueprints/

  Check source/app/iris_engine/access_control/utils.py:407 — the function exists but must be called from the case creation route. If it's
  missing, this is Gap A.

  1b. Confirm ac_auto_update_user_effective_access() handles customer access

  Read source/app/iris_engine/access_control/utils.py around line 482. It must join UserClient → Cases to populate UserCaseEffectiveAccess for
  existing cases when a user's customer list changes. If it only handles group-based or direct-case access, this is Gap B.

  1c. Confirm the POST route returns updated user data

  In manage_users.py:267, the route references data=user but user may be undefined at that scope. Verify the response correctly returns the
  updated user object.

  ---
  Phase 2 — Fix Gap A (if present): Wire Case Creation to Access Control

  If ac_set_new_case_access() isn't called when a case is created:

  File: source/app/blueprints/manage/manage_cases_routes.py (or wherever POST /manage/cases/add lives)

  Change: After the new Cases row is committed to the DB, call:

  from app.iris_engine.access_control.utils import ac_set_new_case_access

  # After case is saved:
  ac_set_new_case_access(
      case_id=new_case.case_id,
      customer_id=new_case.client_id
  )

  This ensures every user currently assigned to that customer immediately gets UserCaseEffectiveAccess rows for the new case.

  ---
  Phase 3 — Fix Gap B (if present): Customer → Existing Cases in Recompute

  If ac_auto_update_user_effective_access() doesn't factor in UserClient when recomputing:

  File: source/app/iris_engine/access_control/utils.py (~line 482)

  Add this block inside the recompute function after clearing stale effective access:

  # Grant access to all cases belonging to the user's assigned customers
  user_clients = UserClient.query.filter(
      UserClient.user_id == user_id
  ).with_entities(UserClient.client_id, UserClient.access_level).all()

  for uc in user_clients:
      customer_cases = Cases.query.filter(
          Cases.client_id == uc.client_id
      ).with_entities(Cases.case_id).all()

      for case in customer_cases:
          ac_add_user_effective_access(
              user_id=user_id,
              case_id=case.case_id,
              access_level=uc.access_level
          )

  This handles existing cases when an admin assigns a customer to a user after those cases were already created.

  ---
  Phase 4 — Alembic Migration (if schema changes are needed)

  The UserClient and UserCaseEffectiveAccess tables already exist per the schema. No migration needed unless Phase 2/3 reveals a missing column.

  If any schema change is required:

  alembic -c app/alembic.ini revision -m "Add customer access level column"

  ---
  Phase 5 — UI Verification

  The customers tab and Manage modal already exist. Verify these three things in the browser:

  1. Modal loads customer list correctly — GET /manage/users/<id>/customers/modal should return all customers (admin sees all, non-admin sees
  only their own)
  2. Save triggers recompute — After clicking save in the modal, the user's case list should immediately reflect the new customer filter
  3. Case list filters correctly — Log in as the target user and confirm GET /manage/cases/filter only returns cases belonging to assigned
  customers

  ---
  Phase 6 — Edge Cases to Handle

  ┌────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │          Scenario          │                                               Where to handle                                               │
  ├────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Admin removes a customer   │ update_user_customers() already deletes UserClient rows and calls recompute — verify the recompute also     │
  │ from a user                │ removes stale UserCaseEffectiveAccess rows                                                                  │
  ├────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ User has no customers      │ user_list_cases_view() returns empty list → case list returns empty — this is correct behavior but confirm  │
  │ assigned                   │ the UI shows a clear empty state rather than an error                                                       │
  ├────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ User is also a server      │ check_ua_case_client() already short-circuits to full access for admins — no change needed                  │
  │ admin                      │                                                                                                             │
  ├────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Case is moved to a         │ If Cases.client_id can be updated, trigger ac_set_new_case_access() for the new customer and strip old      │
  │ different customer         │ access — find the case update route and add this                                                            │
  └────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Execution Order

  1. Read ac_set_new_case_access call sites (grep -rn "ac_set_new_case_access" source/) — 5 min
  2. Read ac_auto_update_user_effective_access full body — 10 min
  3. Implement Gap A fix if needed — 20 min
  4. Implement Gap B fix if needed — 30 min
  5. Test end-to-end: assign customer → check case list as that user — 15 min
  6. Test new case creation: create case for customer → verify user sees it — 10 min

  The system is roughly 80% built. The two likely gaps are whether ac_set_new_case_access is called on case creation, and whether the recompute
  function handles customer-based access for existing cases. Everything else (UI, DB schema, filter query) is already wired correctly.

  Want me to start with Phase 1 and check those two gaps now?