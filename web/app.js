// 화성ON 프론트 — 인용기반 채팅 + 소스패널 + 처리보조(서류초안)
let LANG = "ko";
let LANGS = {ko:"한국어"};

const EXAMPLES = {
  ko: ["쓰레기는 어떻게 버려요?", "외국인등록 어떻게 해요?", "월급을 못 받았어요", "아이 어린이집 신청"],
  en: ["How do I throw out trash?", "How to register as a foreigner?", "I wasn't paid my wages"],
  vi: ["Đăng ký người nước ngoài thế nào?", "Tôi chưa được trả lương", "Vứt rác thế nào?"],
  zh: ["怎么扔垃圾?", "如何办理外国人登录?", "老板没发工资"],
  th: ["ทิ้งขยะอย่างไร?", "ลงทะเบียนคนต่างชาติอย่างไร?", "ยังไม่ได้รับเงินเดือน"],
  km: ["តើខ្ញុំចុះឈ្មោះជនបរទេសយ៉ាងដូចម្ដេច?", "តើបោះសំរាមយ៉ាងណា?"],
};
const T = { // UI 다국어 라벨
  ko:{ph:"예) 쓰레기는 어떻게 버려요?",send:"전송",sources:"근거 출처",helper:"처리 도우미",
       draft:"초안 작성",make:"초안 생성",copy:"복사",copied:"복사됨!",close:"닫기",typing:"입력 중"},
  en:{ph:"e.g. How do I throw out trash?",send:"Send",sources:"Sources",helper:"Assistant",
       draft:"Draft",make:"Generate",copy:"Copy",copied:"Copied!",close:"Close",typing:"typing"},
};
const tr = (k)=> (T[LANG]||T.ko)[k] || T.ko[k];

const $ = (id) => document.getElementById(id);

async function init(){
  try{
    const h = await (await fetch("/api/health")).json();
    LANGS = h.langs || LANGS;
    $("mode").textContent = h.mode === "ollama" ? `● ${h.gen_model}` : "● MOCK";
    $("mode").style.color = h.mode === "ollama" ? "#34d399" : "#f59e0b";
    $("welcome").textContent += `  (지식: 민원 ${h.l1}건 · 자치법규 ${h.l2.toLocaleString()}조문)`;
  }catch(e){ $("mode").textContent = "● 서버오류"; }
  renderLangs(); renderExamples(); applyLabels();
}

function applyLabels(){
  $("input").placeholder = tr("ph");
  $("send").textContent = tr("send");
  $("h-sources").textContent = "📎 " + tr("sources");
  $("h-helper").textContent = "⚡ " + tr("helper");
}

function renderLangs(){
  $("langs").innerHTML = "";
  for(const [code,name] of Object.entries(LANGS)){
    const b = document.createElement("button");
    b.className = "lang" + (code===LANG?" active":"");
    b.textContent = name;
    b.onclick = ()=>{ LANG=code; renderLangs(); renderExamples(); applyLabels(); };
    $("langs").appendChild(b);
  }
}
function renderExamples(){
  const ex = EXAMPLES[LANG] || EXAMPLES.ko;
  $("examples").innerHTML = "";
  ex.forEach(t=>{
    const c = document.createElement("span");
    c.className="ex"; c.textContent=t;
    c.onclick=()=>{ $("input").value=t; send(); };
    $("examples").appendChild(c);
  });
}

function addMsg(text, who){
  const wrap=document.createElement("div"); wrap.className="msg "+who;
  const b=document.createElement("div"); b.className="bubble";
  if(who==="bot"){ b.innerHTML=renderCitations(text); } else { b.textContent=text; }
  wrap.appendChild(b); $("messages").appendChild(wrap);
  $("messages").scrollTop=$("messages").scrollHeight;
  return b;
}

function renderCitations(text){
  const esc = text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  return esc.replace(/\[([a-z]+-[a-z]+-\d+|ord-[\w-]+)\]/g,
    (m,id)=>`<span class="cite" data-id="${id}" onclick="flashCite('${id}')">${id}</span>`);
}
window.flashCite=(id)=>{
  const el=document.querySelector(`.cit-card[data-id="${id}"]`);
  if(el){ el.scrollIntoView({behavior:"smooth",block:"center"});
    el.classList.add("flash"); setTimeout(()=>el.classList.remove("flash"),1500); }
};

function renderSidePanel(citations, actions){
  const c=$("citations"); c.className=""; c.innerHTML="";
  if(!citations.length){ c.className="citations-empty"; c.textContent="관련 근거를 찾지 못했습니다."; }
  citations.forEach(ci=>{
    const d=document.createElement("div"); d.className="cit-card"; d.dataset.id=ci.id;
    d.innerHTML=`<div><span class="cit-id">[${ci.id}]</span>
      <span class="cit-layer ${ci.layer.toLowerCase()}">${ci.layer==="L1"?"민원":"법령"}</span>
      ${ci.confidence?`<span class="conf ${ci.confidence}">${ci.confidence}</span>`:""}</div>
      <div class="cit-title">${ci.title}</div>
      <div class="cit-snip">${ci.snippet}</div>
      ${ci.dept?`<div class="cit-meta">🏛️ ${ci.dept} ${ci.phone?("· "+ci.phone):""}</div>`:""}
      ${ci.source?`<div class="cit-src">${ci.source.replace(/\[([^\]]+)\]\(([^)]+)\)/,'<a href="$2" target="_blank">$1</a>')}</div>`:""}`;
    c.appendChild(d);
  });
  const a=$("actions"); a.className=""; a.innerHTML="";
  if(!actions.length){ a.className="actions-empty"; a.textContent="—"; }
  actions.forEach(ac=>{
    if(ac.type==="link"){
      const el=document.createElement("a"); el.className="act link"; el.href=ac.url; el.target="_blank";
      el.innerHTML=`<b>🔗 ${ac.label}</b><span class="url">${ac.url}</span>`; a.appendChild(el);
    }else if(ac.type==="checklist"){
      const el=document.createElement("div"); el.className="act checklist";
      el.innerHTML=`<b>🗂️ ${ac.title}</b><ul>${ac.items.map(i=>`<li>${i}</li>`).join("")}</ul>`;
      a.appendChild(el);
    }else if(ac.type==="form"){
      const el=document.createElement("button"); el.className="act form";
      el.innerHTML=`<b>📝 ${ac.title} — ${tr("draft")}</b><span class="url">${ac.desc||""}</span>`;
      el.onclick=()=>openDraft(ac); a.appendChild(el);
    }
  });
}

// ── 서류초안 모달 ───────────────────────────────
function openDraft(form){
  const m=$("modal"); m.classList.add("open");
  $("modal-title").textContent = "📝 " + form.title;
  $("modal-desc").textContent = form.desc||"";
  const body=$("modal-body"); body.innerHTML="";
  form.fields.forEach(f=>{
    const row=document.createElement("label"); row.className="field";
    row.innerHTML=`<span>${f.label}</span><input data-key="${f.key}" placeholder="${f.ph||''}">`;
    body.appendChild(row);
  });
  $("modal-result").style.display="none"; $("modal-result").value="";
  $("modal-make").textContent = tr("make");
  $("modal-make").onclick=()=>genDraft(form.domain);
  $("modal-copy").style.display="none";
}
window.closeModal=()=>$("modal").classList.remove("open");
async function genDraft(domain){
  const fields={};
  $("modal-body").querySelectorAll("input").forEach(i=>fields[i.dataset.key]=i.value);
  const today=new Date().toLocaleDateString("ko-KR",{year:"numeric",month:"long",day:"numeric"});
  $("modal-make").disabled=true; $("modal-make").textContent="...";
  try{
    const r=await fetch("/api/draft",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({domain,fields,lang:LANG,today})});
    const d=await r.json();
    const ta=$("modal-result"); ta.style.display="block"; ta.value=d.draft||d.error||"";
    ta.style.height="auto"; ta.style.height=Math.min(ta.scrollHeight+4,420)+"px";
    const cp=$("modal-copy"); cp.style.display="inline-block"; cp.textContent=tr("copy");
    cp.onclick=()=>{ navigator.clipboard.writeText(ta.value); cp.textContent=tr("copied"); };
  }catch(e){ $("modal-result").style.display="block"; $("modal-result").value="오류: "+e; }
  finally{ $("modal-make").disabled=false; $("modal-make").textContent=tr("make"); }
}

// ── 전송 ───────────────────────────────
let busy=false;
async function send(){
  const text=$("input").value.trim();
  if(!text||busy) return;
  busy=true; $("send").disabled=true;
  addMsg(text,"user"); $("input").value="";
  const t=addMsg("","bot");
  t.innerHTML=`<span class="typing"><i></i><i></i><i></i></span>`;
  try{
    const res=await fetch("/api/chat",{method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:text,lang:LANG})});
    const data=await res.json();
    t.innerHTML=renderCitations(data.answer);
    renderSidePanel(data.citations||[], data.actions||[]);
  }catch(e){ t.textContent="서버 오류: "+e; }
  finally{ busy=false; $("send").disabled=false; $("input").focus(); }
}

$("composer").addEventListener("submit",(e)=>{e.preventDefault();send();});
init();
