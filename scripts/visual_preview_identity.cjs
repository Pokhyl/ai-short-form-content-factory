// Reuse preview bytes only when ordered source identities are unchanged.
function identity(c){return ['provider','provider_asset_id','media_type','preview_url','download_url'].map(k=>c[k]??null);}
function samePreviewSources(before,after){return before.length===after.length&&before.every((c,i)=>JSON.stringify(identity(c))===JSON.stringify(identity(after[i])));}
module.exports={samePreviewSources};
