// 화성ON 프론트 — 인용기반 채팅 + 근거 소스패널 + 처리 도우미(서류초안)
let LANG = "ko";
let LANGS = {ko:"한국어"};
let HEALTH = {l1:37, l2:11268};
let STARTED = false; // 첫 질문 이후 히어로 제거

// 언어 코드 배지(국기 이모지는 OS별 렌더가 달라 코드 배지로 통일)
const CODES = {ko:"KO", en:"EN", zh:"ZH", vi:"VI", th:"TH", km:"KM"};

// UI 라벨 다국어
const T = {
  ko:{brand:"외국인 생활민원 AI 안내사", send:"전송", ph:"예) 쓰레기는 어떻게 버려요?",
      sources:"근거 출처", srcHint:"답변의 [번호]를 누르면 강조됩니다", helper:"처리 도우미",
      quick:"자주 묻는 질문", draft:"초안 작성", make:"초안 생성", copy:"복사", copied:"복사됨!",
      hbadge:"화성시 공식 자료 기반 · 6개 언어",
      htitle:"화성에서의 생활,\n<em>모국어로</em> 물어보세요.",
      hlead:"체류·노무·건강보험·쓰레기 배출·보육·운전면허까지 — 화성시 공식 자료에 근거해 답하고, 출처와 신청 방법까지 안내합니다.",
      sL1:"생활민원 FAQ", sL2:"자치법규 조문", sLang:"지원 언어",
      welcome:"안녕하세요! 화성시 생활민원을 도와드립니다. 무엇이든 물어보세요."},
  en:{brand:"AI Living Guide for Foreign Residents", send:"Send", ph:"e.g. How do I throw out trash?",
      sources:"Sources", srcHint:"Tap a [number] in the answer to highlight", helper:"Assistant",
      quick:"Frequently asked", draft:"Draft", make:"Generate", copy:"Copy", copied:"Copied!",
      hbadge:"Based on Hwaseong official data · 6 languages",
      htitle:"Living in Hwaseong —\nask in <em>your language</em>.",
      hlead:"Visa, wages, health insurance, waste disposal, childcare, driver's license — answered from Hwaseong's official sources, with citations and how-to-apply links.",
      sL1:"Living FAQs", sL2:"Ordinance articles", sLang:"Languages",
      welcome:"Hello! I can help with civil affairs in Hwaseong. Ask me anything."},
  zh:{brand:"外国居民生活民愿 AI 向导", send:"发送", ph:"例)垃圾怎么扔?",
      sources:"依据来源", srcHint:"点击答复中的[编号]可高亮", helper:"办理助手",
      quick:"常见问题", draft:"起草", make:"生成草稿", copy:"复制", copied:"已复制!",
      hbadge:"基于华城市官方资料 · 6种语言",
      htitle:"在华城的生活,\n用<em>母语</em>提问。",
      hlead:"居留、工资、医保、垃圾分类、托育、驾照 —— 依据华城市官方资料解答,并提供来源和办理方式。",
      sL1:"生活问答", sL2:"自治法规条文", sLang:"支持语言",
      welcome:"您好!我来帮您处理华城市的生活民愿。请随时提问。"},
  vi:{brand:"Trợ lý AI dịch vụ dân sinh cho người nước ngoài", send:"Gửi", ph:"VD) Vứt rác thế nào?",
      sources:"Nguồn căn cứ", srcHint:"Nhấn [số] trong câu trả lời để làm nổi bật", helper:"Trợ lý thủ tục",
      quick:"Câu hỏi thường gặp", draft:"Soạn thảo", make:"Tạo bản nháp", copy:"Sao chép", copied:"Đã chép!",
      hbadge:"Dựa trên dữ liệu chính thức của Hwaseong · 6 ngôn ngữ",
      htitle:"Cuộc sống ở Hwaseong —\nhãy hỏi bằng <em>tiếng mẹ đẻ</em>.",
      hlead:"Cư trú, tiền lương, bảo hiểm y tế, đổ rác, giữ trẻ, bằng lái — trả lời dựa trên nguồn chính thức của Hwaseong, kèm trích dẫn và cách nộp đơn.",
      sL1:"Hỏi đáp dân sinh", sL2:"Điều luật địa phương", sLang:"Ngôn ngữ",
      welcome:"Xin chào! Tôi hỗ trợ dịch vụ dân sinh ở Hwaseong. Hãy hỏi bất cứ điều gì."},
  th:{brand:"ผู้ช่วย AI บริการประชาชนสำหรับชาวต่างชาติ", send:"ส่ง", ph:"เช่น) ทิ้งขยะอย่างไร?",
      sources:"แหล่งอ้างอิง", srcHint:"แตะ [หมายเลข] ในคำตอบเพื่อไฮไลต์", helper:"ผู้ช่วยดำเนินการ",
      quick:"คำถามที่พบบ่อย", draft:"ร่างเอกสาร", make:"สร้างร่าง", copy:"คัดลอก", copied:"คัดลอกแล้ว!",
      hbadge:"อ้างอิงข้อมูลทางการของฮวาซอง · 6 ภาษา",
      htitle:"ใช้ชีวิตในฮวาซอง —\nถามเป็น<em>ภาษาของคุณ</em>ได้เลย",
      hlead:"วีซ่า ค่าจ้าง ประกันสุขภาพ การทิ้งขยะ การดูแลเด็ก ใบขับขี่ — ตอบจากแหล่งข้อมูลทางการของฮวาซอง พร้อมอ้างอิงและวิธียื่นเรื่อง",
      sL1:"คำถามชีวิตประจำวัน", sL2:"ข้อบัญญัติท้องถิ่น", sLang:"ภาษา",
      welcome:"สวัสดีค่ะ! ยินดีช่วยเรื่องบริการประชาชนในฮวาซอง สอบถามได้เลย"},
  km:{brand:"ជំនួយការ AI សេវាប្រជាពលរដ្ឋសម្រាប់ជនបរទេស", send:"ផ្ញើ", ph:"ឧ) តើបោះសំរាមយ៉ាងណា?",
      sources:"ប្រភពយោង", srcHint:"ចុច[លេខ]ក្នុងចម្លើយដើម្បីបន្លិច", helper:"ជំនួយការនីតិវិធី",
      quick:"សំណួរញឹកញាប់", draft:"ព្រាង", make:"បង្កើតព្រាង", copy:"ចម្លង", copied:"បានចម្លង!",
      hbadge:"ផ្អែកលើទិន្នន័យផ្លូវការ Hwaseong · ៦ ភាសា",
      htitle:"ការរស់នៅក្នុង Hwaseong —\nសួរជា<em>ភាសាកំណើត</em>របស់អ្នក។",
      hlead:"ការស្នាក់នៅ ប្រាក់ឈ្នួល ធានារ៉ាប់រងសុខភាព ការបោះសំរាម ការថែទាំកុមារ ប័ណ្ណបើកបរ — ឆ្លើយតាមប្រភពផ្លូវការ Hwaseong ព្រមទាំងប្រភព និងវិធីដាក់ពាក្យ។",
      sL1:"សំណួរ​ជីវភាព", sL2:"បទប្បញ្ញត្តិមូលដ្ឋាន", sLang:"ភាសា",
      welcome:"សួស្តី! ខ្ញុំជួយសេវាប្រជាពលរដ្ឋនៅ Hwaseong។ សួរបានគ្រប់ពេល។"},
};
// 랜딩 보조 라벨(빈 패널/주의문/모드) 다국어
const EXTRA = {
  ko:{emptyCit:"질문하면 답변의 근거가 여기에 표시됩니다.", emptyAct:"필요서류·신청 링크·서류 초안이 여기에 표시됩니다.",
      disc:"⚠️ 안내는 참고용입니다. 최종 확인은 담당기관에 문의하세요.<br>🔒 개인정보·인증정보는 저장하지 않습니다.",
      demo:"데모 모드", live:"실시간 AI", srvErr:"서버 오류", download:"📥 다운로드"},
  en:{emptyCit:"Citations for the answer will appear here.", emptyAct:"Required documents, apply links and draft forms appear here.",
      disc:"⚠️ This guidance is for reference only. Please confirm with the responsible office.<br>🔒 No personal or credential data is stored.",
      demo:"Demo mode", live:"Live AI", srvErr:"Server error", download:"📥 Download"},
  zh:{emptyCit:"答复的依据将显示在此处。", emptyAct:"所需材料、申请链接和文书草稿将显示在此处。",
      disc:"⚠️ 本指引仅供参考,请向主管部门最终确认。<br>🔒 不保存个人信息及认证信息。",
      demo:"演示模式", live:"实时 AI", srvErr:"服务器错误", download:"📥 下载"},
  vi:{emptyCit:"Căn cứ của câu trả lời sẽ hiển thị ở đây.", emptyAct:"Giấy tờ cần thiết, liên kết nộp đơn và bản nháp sẽ hiển thị ở đây.",
      disc:"⚠️ Thông tin chỉ mang tính tham khảo. Vui lòng xác nhận với cơ quan phụ trách.<br>🔒 Không lưu thông tin cá nhân hoặc xác thực.",
      demo:"Chế độ demo", live:"AI trực tiếp", srvErr:"Lỗi máy chủ", download:"📥 Tải về"},
  th:{emptyCit:"แหล่งอ้างอิงของคำตอบจะแสดงที่นี่", emptyAct:"เอกสารที่ต้องใช้ ลิงก์ยื่นเรื่อง และร่างเอกสารจะแสดงที่นี่",
      disc:"⚠️ ข้อมูลนี้ใช้เพื่ออ้างอิงเท่านั้น โปรดยืนยันกับหน่วยงานที่รับผิดชอบ<br>🔒 ไม่จัดเก็บข้อมูลส่วนบุคคลหรือข้อมูลยืนยันตัวตน",
      demo:"โหมดสาธิต", live:"AI สด", srvErr:"เซิร์ฟเวอร์ผิดพลาด", download:"📥 ดาวน์โหลด"},
  km:{emptyCit:"ប្រភពនៃចម្លើយនឹងបង្ហាញនៅទីនេះ។", emptyAct:"ឯកសារចាំបាច់ តំណដាក់ពាក្យ និងសេចក្ដីព្រាងនឹងបង្ហាញនៅទីនេះ។",
      disc:"⚠️ ព័ត៌មាននេះសម្រាប់ជាឯកសារយោងប៉ុណ្ណោះ។ សូមបញ្ជាក់ជាមួយស្ថាប័នទទួលបន្ទុក។<br>🔒 មិនរក្សាទុកព័ត៌មានផ្ទាល់ខ្លួន ឬព័ត៌មានផ្ទៀងផ្ទាត់ឡើយ។",
      demo:"របៀបសាកល្បង", live:"AI ផ្ទាល់", srvErr:"កំហុសម៉ាស៊ីនមេ", download:"📥 ទាញយក"},
};
Object.keys(EXTRA).forEach(l=>{ T[l]=Object.assign(T[l]||{}, EXTRA[l]); });
const tr = (k) => (T[LANG] || T.ko)[k] || T.ko[k];

// 주제 카드(8 도메인). 제목/질문은 언어별, 없으면 ko/en로 폴백.
const TOPICS = [
  {ic:"🪪", t:{ko:"체류·외국인등록",en:"Visa & Registration",zh:"居留登记",vi:"Cư trú",th:"วีซ่า",km:"ស្នាក់នៅ"},
   q:{ko:"외국인등록 어떻게 해요?",en:"How do I register as a foreigner?",zh:"如何办理外国人登录?",vi:"Đăng ký người nước ngoài thế nào?",th:"ลงทะเบียนคนต่างชาติอย่างไร?",km:"តើខ្ញុំចុះឈ្មោះជនបរទេសយ៉ាងដូចម្ដេច?"}},
  {ic:"💼", t:{ko:"임금·노무",en:"Wages & Labor",zh:"工资劳务",vi:"Tiền lương",th:"ค่าจ้าง",km:"ប្រាក់ឈ្នួល"},
   q:{ko:"월급을 못 받았어요",en:"I wasn't paid my wages",zh:"老板没发工资",vi:"Tôi chưa được trả lương",th:"ยังไม่ได้รับเงินเดือน",km:"ខ្ញុំមិនបានទទួលប្រាក់ឈ្នួល"}},
  {ic:"🏥", t:{ko:"건강보험·의료",en:"Health Insurance",zh:"医疗保险",vi:"Bảo hiểm y tế",th:"ประกันสุขภาพ",km:"ធានារ៉ាប់រង"},
   q:{ko:"건강보험 어떻게 가입해요?",en:"How do I join health insurance?",zh:"如何加入健康保险?",vi:"Đăng ký bảo hiểm y tế thế nào?",th:"สมัครประกันสุขภาพอย่างไร?",km:"តើចូលរួមធានារ៉ាប់រងសុខភាពយ៉ាងណា?"}},
  {ic:"🗑️", t:{ko:"쓰레기·폐기물",en:"Waste Disposal",zh:"垃圾处理",vi:"Đổ rác",th:"การทิ้งขยะ",km:"សំរាម"},
   q:{ko:"쓰레기는 어떻게 버려요?",en:"How do I throw out trash?",zh:"垃圾怎么扔?",vi:"Vứt rác thế nào?",th:"ทิ้งขยะอย่างไร?",km:"តើបោះសំរាមយ៉ាងណា?"}},
  {ic:"🧸", t:{ko:"보육·교육",en:"Childcare & School",zh:"托育教育",vi:"Giữ trẻ",th:"ดูแลเด็ก",km:"ថែទាំកុមារ"},
   q:{ko:"아이 어린이집 신청하고 싶어요",en:"I want to apply for daycare",zh:"想申请幼儿园",vi:"Tôi muốn đăng ký nhà trẻ",th:"อยากสมัครรับเลี้ยงเด็ก",km:"ខ្ញុំចង់ដាក់ពាក្យមត្តេយ្យ"}},
  {ic:"🚗", t:{ko:"운전면허",en:"Driver's License",zh:"驾照",vi:"Bằng lái",th:"ใบขับขี่",km:"ប័ណ្ណបើកបរ"},
   q:{ko:"외국인 운전면허 어떻게 따요?",en:"How can a foreigner get a driver's license?",zh:"外国人如何考驾照?",vi:"Người nước ngoài lấy bằng lái thế nào?",th:"ชาวต่างชาติทำใบขับขี่อย่างไร?",km:"តើជនបរទេសយកប័ណ្ណបើកបរយ៉ាងណា?"}},
  {ic:"📋", t:{ko:"행정·전입",en:"Move-in Report",zh:"行政迁入",vi:"Khai báo cư trú",th:"แจ้งย้ายเข้า",km:"រដ្ឋបាល"},
   q:{ko:"전입신고 어떻게 해요?",en:"How do I report a move-in?",zh:"如何办理迁入申报?",vi:"Khai báo chuyển đến thế nào?",th:"แจ้งย้ายเข้าอย่างไร?",km:"តើរាយការណ៍ផ្លាស់ចូលយ៉ាងណា?"}},
  {ic:"🤝", t:{ko:"외국인 지원기관",en:"Support Centers",zh:"支援机构",vi:"Trung tâm hỗ trợ",th:"ศูนย์ช่วยเหลือ",km:"មជ្ឈមណ្ឌលជំនួយ"},
   q:{ko:"외국인 상담은 어디서 받아요?",en:"Where can I get counseling for foreigners?",zh:"外国人在哪里咨询?",vi:"Người nước ngoài tư vấn ở đâu?",th:"ปรึกษาสำหรับชาวต่างชาติได้ที่ไหน?",km:"តើជនបរទេសពិគ្រោះនៅឯណា?"}},
];
const pick = (obj) => obj[LANG] || obj.en || obj.ko;

const $ = (id) => document.getElementById(id);

async function init(){
  try{
    const h = await (await fetch("/api/health")).json();
    HEALTH = h; LANGS = h.langs || LANGS;
  }catch(e){ HEALTH = {error:true}; }
  renderLangs(); applyLabels(); renderHero(); renderExamples();
}

function renderMode(){
  const el = $("mode");
  if(HEALTH.error){ el.innerHTML = `<span style="color:#ef4444">●</span> ${tr("srvErr")}`; return; }
  el.innerHTML = HEALTH.mode === "ollama"
    ? `<span style="color:#10b981">●</span> ${tr("live")} · ${HEALTH.gen_model}`
    : `<span style="color:#f59e0b">●</span> ${tr("demo")}`;
}

function applyLabels(){
  document.documentElement.lang = LANG;
  $("brand-title").textContent = tr("brand");
  $("input").placeholder = tr("ph");
  $("send-label").textContent = tr("send");
  $("h-sources").querySelector("span:nth-child(2)").textContent = tr("sources");
  $("h-sources-hint").textContent = tr("srcHint");
  $("h-helper").querySelector("span:nth-child(2)").textContent = tr("helper");
  $("quick-label").textContent = tr("quick");
  $("disclaimer").innerHTML = tr("disc");
  if(!STARTED){
    $("citations").className = "empty-box"; $("citations").textContent = tr("emptyCit");
    $("actions").className = "empty-box"; $("actions").textContent = tr("emptyAct");
  }
  renderMode();
}

function renderLangs(){
  $("langs").innerHTML = "";
  for(const [code,name] of Object.entries(LANGS)){
    const b = document.createElement("button");
    b.className = "lang" + (code===LANG ? " active" : "");
    b.innerHTML = `<span class="flag">${CODES[code]||code.toUpperCase()}</span>${name}`;
    b.onclick = () => { LANG = code; renderLangs(); applyLabels();
      if(!STARTED) renderHero(); renderExamples(); };
    $("langs").appendChild(b);
  }
}

function renderHero(){
  const m = $("messages"); m.innerHTML = "";
  const l1 = (HEALTH.l1||0).toLocaleString();
  const l2 = (HEALTH.l2||0).toLocaleString();
  const nlang = Object.keys(LANGS).length;
  const hero = document.createElement("div");
  hero.className = "hero";
  hero.innerHTML = `
    <span class="hero-badge">✅ ${tr("hbadge")}</span>
    <h1>${tr("htitle")}</h1>
    <p>${tr("hlead")}</p>
    <div class="hero-stats">
      <div class="hstat"><b>${l1}</b><span>${tr("sL1")}</span></div>
      <div class="hstat"><b>${l2}</b><span>${tr("sL2")}</span></div>
      <div class="hstat"><b>${nlang}</b><span>${tr("sLang")}</span></div>
    </div>
    <div class="topics" id="topics"></div>`;
  m.appendChild(hero);
  const grid = hero.querySelector("#topics");
  TOPICS.forEach(tp=>{
    const c = document.createElement("button");
    c.className = "topic";
    c.innerHTML = `<span class="ic">${tp.ic}</span>
      <span class="tl">${pick(tp.t)}</span>`;
    // 주제 카드는 입력창에 채우기만(자동 전송하지 않음) — 사용자가 확인 후 전송
    c.onclick = () => { const i=$("input"); i.value = pick(tp.q); i.focus(); };
    grid.appendChild(c);
  });
}

function renderExamples(){
  const ex = TOPICS.slice(0,5).map(tp=>pick(tp.q));
  $("examples").innerHTML = "";
  ex.forEach(t=>{
    const c = document.createElement("span");
    c.className="ex"; c.textContent=t;
    c.onclick=()=>{ $("input").value=t; send(); };
    $("examples").appendChild(c);
  });
}

function addMsg(text, who){
  if(!STARTED){ STARTED=true; $("messages").innerHTML=""; }
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
    el.classList.add("flash"); setTimeout(()=>el.classList.remove("flash"),1600); }
};

function renderSidePanel(citations, actions){
  const c=$("citations"); c.className=""; c.innerHTML="";
  if(!citations.length){ c.className="empty-box"; c.textContent="관련 근거를 찾지 못했습니다."; }
  citations.forEach(ci=>{
    const d=document.createElement("div"); d.className="cit-card"+(ci.kind==="법적근거"?" legal":""); d.dataset.id=ci.id;
    const layerLabel = ci.kind==="법적근거" ? "⚖️ 법적 근거" : (ci.layer==="L1"?"민원 FAQ":"자치법규");
    d.innerHTML=`<div class="cit-top"><span class="cit-id">[${ci.id}]</span>
      <span class="cit-layer ${ci.layer.toLowerCase()}">${layerLabel}</span>
      ${ci.confidence?`<span class="conf ${ci.confidence}">${ci.confidence}</span>`:""}</div>
      <div class="cit-title">${ci.title}</div>
      <div class="cit-snip">${ci.snippet}</div>
      ${ci.dept?`<div class="cit-meta">🏛️ ${ci.dept}${ci.phone?(" · "+ci.phone):""}</div>`:""}
      ${ci.source?`<div class="cit-src">${ci.source.replace(/\[([^\]]+)\]\(([^)]+)\)/,'<a href="$2" target="_blank" rel="noopener">$1 ↗</a>')}</div>`:""}`;
    c.appendChild(d);
  });
  const a=$("actions"); a.className=""; a.innerHTML="";
  if(!actions.length){ a.className="empty-box"; a.textContent="해당 질문에는 추가 처리 항목이 없습니다."; }
  actions.forEach(ac=>{
    if(ac.type==="info"){
      const el=document.createElement("div"); el.className="act info";
      el.innerHTML=`<b>🧭 ${ac.title}</b><ul>${ac.items.map(i=>`<li>${i}</li>`).join("")}</ul>`;
      a.appendChild(el);
    }else if(ac.type==="policy"){
      const el=document.createElement("div"); el.className="act policy";
      el.innerHTML=`<b>💡 ${ac.title}</b>`+ac.items.map(p=>
        `<a class="pol" href="${p.url}" target="_blank" rel="noopener">
           <span class="pol-n">${p.name} ↗</span>
           <span class="pol-d">${p.desc}</span></a>`).join("");
      a.appendChild(el);
    }else if(ac.type==="link"){
      const el=document.createElement("a"); el.className="act link"; el.href=ac.url; el.target="_blank"; el.rel="noopener";
      el.innerHTML=`<b>🔗 ${ac.label}</b><span class="url">${ac.url} ↗</span>`; a.appendChild(el);
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
let CUR_DRAFT_TITLE = "서류초안";
let CUR_DRAFT_DOMAIN = "";
function openDraft(form){
  const m=$("modal"); m.classList.add("open");
  CUR_DRAFT_TITLE = form.title || "서류초안";
  CUR_DRAFT_DOMAIN = form.domain || "";
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
  $("modal-download").style.display="none";
  $("modal-docx").style.display="none";
  $("modal-hwpx").style.display="none";
}
function _safeName(){ return CUR_DRAFT_TITLE.replace(/[\\/:*?"<>|]/g,"").replace(/\s+/g,"_"); }
function _today(){ return new Date().toISOString().slice(0,10); }
function downloadDraft(){
  const text=$("modal-result").value; if(!text) return;
  const blob=new Blob([text],{type:"text/plain;charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download=`${_safeName()}_${_today()}.txt`;
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}
async function downloadFile(kind, ext, btnId, label){
  const fields={};
  $("modal-body").querySelectorAll("input").forEach(i=>fields[i.dataset.key]=i.value);
  const today=new Date().toLocaleDateString("ko-KR",{year:"numeric",month:"long",day:"numeric"});
  const btn=$(btnId); const prev=btn.textContent; btn.disabled=true; btn.textContent="…";
  try{
    const r=await fetch(`/api/draft/${kind}`,{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({domain:CUR_DRAFT_DOMAIN,fields,lang:LANG,today})});
    if(!r.ok) throw new Error(label+" 생성 실패");
    const blob=await r.blob(); const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url; a.download=`${_safeName()}_${_today()}.${ext}`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }catch(e){ alert(label+" 다운로드 오류: "+e); }
  finally{ btn.disabled=false; btn.textContent=prev; }
}
const downloadHwpx=()=>downloadFile("hwpx","hwpx","modal-hwpx","HWPX");
const downloadDocx=()=>downloadFile("docx","docx","modal-docx","Word");
window.closeModal=()=>$("modal").classList.remove("open");
async function genDraft(domain){
  const fields={};
  $("modal-body").querySelectorAll("input").forEach(i=>fields[i.dataset.key]=i.value);
  const today=new Date().toLocaleDateString("ko-KR",{year:"numeric",month:"long",day:"numeric"});
  $("modal-make").disabled=true; $("modal-make").textContent="…";
  try{
    const r=await fetch("/api/draft",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({domain,fields,lang:LANG,today})});
    const d=await r.json();
    const ta=$("modal-result"); ta.style.display="block"; ta.value=d.draft||d.error||"";
    ta.style.height="auto"; ta.style.height=Math.min(ta.scrollHeight+4,440)+"px";
    const cp=$("modal-copy"); cp.style.display="inline-block"; cp.textContent=tr("copy");
    cp.onclick=()=>{ navigator.clipboard.writeText(ta.value); cp.textContent=tr("copied"); };
    const hx=$("modal-hwpx"); hx.style.display="inline-block"; hx.onclick=downloadHwpx;
    const dl=$("modal-download"); dl.style.display="inline-block"; dl.onclick=downloadDraft;
    const dx=$("modal-docx"); dx.style.display="inline-block"; dx.onclick=downloadDocx;
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
document.addEventListener("keydown",(e)=>{ if(e.key==="Escape") closeModal(); });
init();
