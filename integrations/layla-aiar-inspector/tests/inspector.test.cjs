"use strict";
const test=require("node:test"), assert=require("node:assert/strict");
const {normalizeDigest,inspectReceipt}=require("../core.js");
const good=()=>({
 receipt_id:"r1",trace_id:"t1",record_schema_version:"0.1",receipt_version:"0.1",
 system:{agent_id:"Taylor Moon",version:"1"},authority:{principal:"owner",delegate:"Taylor Moon",scope:["read"],prohibited:["send_email"],valid_from:"2026-10-20T02:00:00-04:00",valid_until:"2026-10-20T03:00:00-04:00"},
 material_sources:[{source_id:"s1",role:"support"}],
 material_actions:[{event_id:"e1",operation:"read",status:"completed",authorization:"not_required",consequential:false,occurred_at:"2026-10-20T02:10:00-04:00",source_refs:["s1"]}],
 verification:{state:"pending"},incidents:[],
 integrity:{record_hash:"sha256:fixture",derived_from_record_hash:"sha256:fixture",generated_at:"2026-10-20T02:20:00-04:00"}
});
test("basic candidate has no issues",()=>assert.deepEqual(inspectReceipt(good()).issues,[]));
test("null and empty inputs fail",()=>{assert.ok(inspectReceipt(null).issues.length);assert.ok(inspectReceipt({}).issues.length);});
test("unauthorized consequential completion flagged",()=>{const r=good();r.material_actions[0].consequential=true;assert.match(inspectReceipt(r).issues.join(" "),/not approved/);});
test("authorization after execution flagged",()=>{const r=good();Object.assign(r.material_actions[0],{consequential:true,authorization:"approved",authorization_decided_at:"2026-10-20T02:30:00-04:00"});assert.match(inspectReceipt(r).issues.join(" "),/after execution/);});
test("prohibited completed action flagged",()=>{const r=good();r.material_actions[0].operation="send_email";assert.match(inspectReceipt(r).issues.join(" "),/Prohibited/);});
test("unregistered source flagged",()=>{const r=good();r.material_actions[0].source_refs=["invalid"];assert.match(inspectReceipt(r).issues.join(" "),/Unknown source/);});
test("blocked denied requires incident",()=>{const r=good();Object.assign(r.material_actions[0],{status:"blocked",authorization:"denied"});assert.match(inspectReceipt(r).issues.join(" "),/Missing blocked incident/);r.incidents=[{type:"blocked",event_id:"e1"}];assert.doesNotMatch(inspectReceipt(r).issues.join(" "),/Missing blocked incident/);});
test("confirmed requires verification evidence",()=>{const r=good();r.verification.state="confirmed";assert.match(inspectReceipt(r).issues.join(" "),/Confirmed without evidence/);});
test("SHA-256 normalization",()=>{assert.equal(normalizeDigest("sha256:"+"AA".repeat(32)),"aa".repeat(32));assert.equal(normalizeDigest("bogus"),null);});
