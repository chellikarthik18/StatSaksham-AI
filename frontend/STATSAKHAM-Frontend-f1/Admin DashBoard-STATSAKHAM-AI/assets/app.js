
const API_BASE_URL = "/api";

function toast(message, type="success"){
  const id = "toast-" + Date.now();
  const wrap = document.getElementById("toastContainer");
  if(!wrap) return;
  const icon = type==="success" ? "check-circle" : type==="danger" ? "x-circle" : "info-circle";
  wrap.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
      <div class="d-flex"><div class="toast-body"><i class="bi bi-${icon} me-2"></i>${escapeHtml(message)}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>
    </div>`);
  const el=document.getElementById(id); new bootstrap.Toast(el,{delay:3000}).show();
  el.addEventListener("hidden.bs.toast",()=>el.remove());
}
function escapeHtml(v){
  return String(v ?? "").replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[s]));
}
function showLoading(show=true){
  document.getElementById("loadingOverlay")?.classList.toggle("show",show);
}
async function fetchData(endpoint, options={}){
  const res = await fetch(API_BASE_URL + endpoint, {headers:{"Content-Type":"application/json"}, ...options});
  if(!res.ok) throw new Error(`API request failed (${res.status})`);
  return res.json();
}
async function postData(endpoint,data){
  return fetchData(endpoint,{method:"POST",body:JSON.stringify(data)});
}
async function putData(endpoint,data){
  return fetchData(endpoint,{method:"PUT",body:JSON.stringify(data)});
}
async function deleteData(endpoint){
  return fetchData(endpoint,{method:"DELETE"});
}
function exportTableToCSV(tableId, filename){
  const table=document.getElementById(tableId);
  if(!table){toast("Table not found","danger");return}
  const rows=[...table.querySelectorAll("tr")].map(tr=>[...tr.children].map(td=>`"${td.innerText.replaceAll('"','""')}"`).join(","));
  const blob=new Blob([rows.join("\n")],{type:"text/csv;charset=utf-8"});
  const url=URL.createObjectURL(blob), a=document.createElement("a");
  a.href=url;a.download=filename;a.click();URL.revokeObjectURL(url);
  toast("CSV exported successfully");
}
function bindCommonUI(){
  const currentPage=(location.pathname.split("/").pop()||"dashboard.html").toLowerCase();

  // Keep the selected sidebar item highlighted on every page.
  document.querySelectorAll(".sidebar .nav-link[href]").forEach(el=>{
    const href=(el.getAttribute("href")||"").split("?")[0].split("#")[0].toLowerCase();
    const active=href===currentPage || (currentPage==="" && href==="dashboard.html");
    el.classList.toggle("active",active);
    if(active) el.setAttribute("aria-current","page");
    else el.removeAttribute("aria-current");
    el.addEventListener("click",()=>{
      if(innerWidth<=991) document.getElementById("sidebar")?.classList.remove("mobile-open");
    });
  });

  const sidebar=document.getElementById("sidebar"), main=document.getElementById("mainWrap");
  document.getElementById("sidebarToggle")?.addEventListener("click",()=>{
    if(innerWidth<=991) sidebar?.classList.toggle("mobile-open");
    else {sidebar?.classList.toggle("collapsed");main?.classList.toggle("expanded")}
  });

  // The bell in the header is a real navigation control rather than a dead button.
  document.getElementById("notificationsButton")?.addEventListener("click",()=>{
    window.location.href="notifications.html";
  });

  document.getElementById("globalSearch")?.addEventListener("keydown",e=>{
    if(e.key==="Enter"){
      const q=e.target.value.trim();
      if(q) toast(`Global search submitted: ${q}`,"info");
    }
  });

  // Make table headers sortable wherever the page exposes sort-head columns.
  document.querySelectorAll(".sort-head[data-col]").forEach(head=>{
    head.style.cursor="pointer";
    head.setAttribute("role","button");
    head.setAttribute("tabindex","0");
    let asc=true;
    const sort=()=>{
      const table=head.closest("table");
      if(!table?.id) return;
      tableSort(table.id,Number(head.dataset.col),asc);
      asc=!asc;
    };
    head.addEventListener("click",sort);
    head.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();sort();}});
  });

  document.querySelectorAll("[data-bs-toggle='tooltip']").forEach(x=>new bootstrap.Tooltip(x));
}
function tableSearch(inputId, tableId){
  const input=document.getElementById(inputId), table=document.getElementById(tableId);
  if(!input||!table)return;
  input.addEventListener("input",()=>{
    const q=input.value.toLowerCase();
    table.querySelectorAll("tbody tr").forEach(tr=>tr.style.display=tr.innerText.toLowerCase().includes(q)?"":"none");
  });
}
function tableSort(tableId,colIndex,asc=true){
  const table=document.getElementById(tableId), tbody=table?.querySelector("tbody");
  if(!tbody)return;
  [...tbody.rows].sort((a,b)=>{
    const A=a.cells[colIndex]?.innerText.trim()||"",B=b.cells[colIndex]?.innerText.trim()||"";
    return (A.localeCompare(B,undefined,{numeric:true,sensitivity:"base"}))*(asc?1:-1);
  }).forEach(r=>tbody.appendChild(r));
}
function setPageTitle(title){
  const el=document.getElementById("pageTitle"); if(el) el.textContent=title;
}
function aiOperation(btn, endpoint, payload, onResult){
  const original=btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner-border spinner-border-sm me-2"></span>Processing…';
  postData(endpoint,payload).then(result=>{ onResult?.(result); toast("AI operation completed"); })
    .catch(err=>{toast(err.message || "AI operation failed","danger")})
    .finally(()=>{btn.disabled=false;btn.innerHTML=original});
}
function initCharts(){
  document.querySelectorAll("canvas[data-chart]").forEach(canvas=>{
    const type=canvas.dataset.chart;
    if(type==="competency"){
      new Chart(canvas,{type:"bar",data:{labels:["Statistical","Technical","Digital Governance","Behavioural"],datasets:[{label:"Average Competency %",data:[0,0,0,0]}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,max:100}}}});
    }
    if(type==="department"){
      new Chart(canvas,{type:"bar",data:{labels:["Department A","Department B","Department C","Department D"],datasets:[{label:"Average Competency %",data:[0,0,0,0]}]},options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,max:100}}}});
    }
    if(type==="training"){
      new Chart(canvas,{type:"doughnut",data:{labels:["Not Started","In Progress","Completed"],datasets:[{data:[0,0,0]}]},options:{responsive:true,maintainAspectRatio:false}});
    }
  })
}

document.addEventListener("DOMContentLoaded",()=>{
  bindCommonUI(); initCharts();
  document.querySelectorAll("[data-api-load]").forEach(async el=>{
    const endpoint=el.dataset.apiLoad;
    try{ await fetchData(endpoint); }catch(e){ /* backend may not be running during frontend-only preview */ }
  });
});
