(function(root){
"use strict";
const required=["receipt_id","trace_id","record_schema_version","receipt_version","system","authority","material_sources","material_actions","verification","incidents","integrity"];
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const text=x=>typeof x==="string"&&x.trim().length>0;
const date=x=>typeof x==="string"&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(x)&&Number.isFinite(Date.parse(x));
function normalizeDigest(s){const a=String(s||"").trim().replace(/^sha256:/i,"").toLowerCase();return /^[a-f0-9]{64}$/.test(a)?a:null;}
function inspectReceipt(r){
 const issues=[],warnings=["Advisory checks only; not the full AIAR Schema/semantic validator.","No independent identity, timestamp or process authentication has occurred."];
 if(!obj(r))return {issues:["Receipt must be a JSON object."],warnings,stats:null};
 required.forEach(k=>{if(!(k in r))issues.push("Missing required field: "+k);});
 for(const k of required.slice(0,4))if(!text(r[k]))issues.push("Missing nonempty "+k);
 if(!obj(r.system)||!text(r.system.agent_id)||!text(r.system.version))issues.push("system requires agent_id and version");
 if(!obj(r.authority))issues.push("authority must be an object");
 else {
  if(!text(r.authority.principal)||!text(r.authority.delegate))issues.push("authority needs principal and delegate");
  if(!Array.isArray(r.authority.scope))issues.push("authority scope must be an array");
  if(!date(r.authority.valid_from)||!date(r.authority.valid_until))issues.push("authority dates require timezone offsets");
  else if(Date.parse(r.authority.valid_from)>Date.parse(r.authority.valid_until))issues.push("authority window inverted");
 }
 const sources=Array.isArray(r.material_sources)?r.material_sources:[], actions=Array.isArray(r.material_actions)?r.material_actions:[], incidents=Array.isArray(r.incidents)?r.incidents:[];
 if(!Array.isArray(r.material_sources))issues.push("material_sources must be array");
 if(!Array.isArray(r.material_actions))issues.push("material_actions must be array");
 if(!Array.isArray(r.incidents))issues.push("incidents must be array");
 const srcIds=new Set(), eventIds=new Set();
 sources.forEach((s,i)=>{if(!obj(s)||!text(s.source_id)||!text(s.role))issues.push("Invalid source at "+i);else{if(srcIds.has(s.source_id))issues.push("Duplicate source "+s.source_id);srcIds.add(s.source_id);}});
 actions.forEach((a,i)=>{
  if(!obj(a)||!text(a.event_id)||!text(a.operation)){issues.push("Invalid action "+i);return;}
  if(eventIds.has(a.event_id))issues.push("Duplicate event "+a.event_id);
  eventIds.add(a.event_id);
  if(!["completed","blocked","failed","pending","unknown"].includes(a.status))issues.push("Unknown status at action "+i);
  if(!["approved","denied","not_required","unknown"].includes(a.authorization))issues.push("Unknown authorization at action "+i);
  if(!date(a.occurred_at))issues.push("Missing dated event "+i);
  if(a.consequential===true&&a.status==="completed"){
   if(a.authorization!=="approved")issues.push("Consequential action not approved: "+a.event_id);
   if(!date(a.authorization_decided_at))issues.push("Missing authorization time: "+a.event_id);
   else if(date(a.occurred_at)&&Date.parse(a.authorization_decided_at)>Date.parse(a.occurred_at))issues.push("Authorization after execution: "+a.event_id);
  }
  if(a.status==="completed"&&Array.isArray(r.authority?.prohibited)&&r.authority.prohibited.includes(a.operation))issues.push("Prohibited action completed: "+a.event_id);
  if(a.status==="blocked"&&a.authorization==="denied"&&!incidents.some(e=>obj(e)&&e.event_id===a.event_id))issues.push("Missing blocked incident: "+a.event_id);
  if(Array.isArray(a.source_refs))for(const id of a.source_refs)if(!srcIds.has(id))issues.push("Unknown source reference: "+id);
 });
 if(!obj(r.verification)||!["not_required","pending","confirmed","failed","uncertain"].includes(r.verification.state))issues.push("Invalid verification state");
 else if(r.verification.state==="confirmed"&&(!Array.isArray(r.verification.evidence_refs)||!r.verification.evidence_refs.length))issues.push("Confirmed without evidence_refs");
 if(!obj(r.integrity)||!text(r.integrity.record_hash)||!text(r.integrity.derived_from_record_hash)||!date(r.integrity.generated_at))issues.push("Integrity missing hash or generated_at");
 else if(r.integrity.record_hash!==r.integrity.derived_from_record_hash)issues.push("Record hashes disagree");
 return {issues,warnings,stats:{receipt_id:r.receipt_id||null,agent_id:r.system?.agent_id||null,verification:r.verification?.state||"unknown",sources:sources.length,actions:actions.length,incidents:incidents.length}};
}
const api={normalizeDigest,inspectReceipt};root.AIARCore=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis==="object"?globalThis:this);
