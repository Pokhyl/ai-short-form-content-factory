# 2026-09-11 — stage WF03 import used unsupported activeState mode

The first deployment attempt for the tested WF03 duration-rewrite fix stopped before workflow import because the operator invoked `n8n import:workflow --activeState=fromJson` on this regular n8n deployment. The CLI rejected it: `The --activeState=fromJson flag can only be used when n8n is running in queue or multi-main mode. In regular deployment mode, workflow activation is not supported.`

Readback immediately after the failure proved no workflow version changed: production WF03 remained `bccdbbba-8b8f-4424-8ed5-e7b76de4647a` active/current and stage WF03 remained `1224b902-52b3-4d86-b09a-d9b07bb0ef46` active/current.

No product job was created and no production/runtime workflow mutation occurred. Correction: import the exact stage-ID candidate with the regular import mode, then explicitly publish the new current stage version and verify production WF03 remains unchanged.
