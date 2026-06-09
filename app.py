import logging
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, render_template_string, request, session
from flask_cors import CORS

import database as db
from agent import chat
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key")
CORS(app)

db.init_db()
start_scheduler()

# ── Templates ─────────────────────────────────────────────────────────────────

CHAT_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agente Instagram Autônomo</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#e5e5e5;height:100dvh;display:flex;flex-direction:column}
    header{padding:14px 20px;background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);display:flex;align-items:center;gap:12px;flex-shrink:0}
    header h1{font-size:16px;font-weight:700;color:#fff}
    nav{display:flex;gap:8px;margin-left:auto}
    nav a{color:rgba(255,255,255,.8);font-size:12px;text-decoration:none;padding:4px 10px;border-radius:20px;border:1px solid rgba(255,255,255,.3);transition:all .15s}
    nav a:hover{background:rgba(255,255,255,.15)}
    #chat{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;scrollbar-width:thin;scrollbar-color:#222 transparent}
    .msg{max-width:800px;padding:12px 16px;border-radius:14px;font-size:14px;line-height:1.6;white-space:pre-wrap;word-break:break-word}
    .user{background:#1a1a2e;border:1px solid #2a2a4a;align-self:flex-end;color:#c8c8ff}
    .agent{background:#111;border:1px solid #1e1e1e;align-self:flex-start}
    .thinking{color:#444;font-style:italic;font-size:12px;background:transparent;border:none;padding:2px 0;animation:pulse 1.5s infinite}
    @keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}
    footer{padding:12px 20px;border-top:1px solid #1a1a1a;flex-shrink:0}
    #form{display:flex;gap:8px}
    textarea{flex:1;background:#111;border:1px solid #2a2a2a;border-radius:10px;color:#e5e5e5;padding:10px 14px;font-size:14px;resize:none;min-height:44px;max-height:120px;outline:none;font-family:inherit}
    textarea:focus{border-color:#444}
    button{background:linear-gradient(135deg,#833ab4,#fd1d1d);color:#fff;border:none;border-radius:10px;padding:10px 18px;cursor:pointer;font-size:14px;font-weight:600;flex-shrink:0;transition:opacity .15s}
    button:hover{opacity:.85}
    button:disabled{opacity:.3;cursor:not-allowed}
    .actions{display:flex;gap:12px;margin-top:8px}
    .chip{background:#111;border:1px solid #2a2a2a;color:#888;font-size:12px;padding:5px 12px;border-radius:20px;cursor:pointer;transition:all .15s;white-space:nowrap}
    .chip:hover{border-color:#555;color:#ccc}
    #hint{font-size:11px;color:#333;margin-top:4px}
  </style>
</head>
<body>
<header>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="white" stroke="none"/></svg>
  <h1>Agente Instagram Autônomo</h1>
  <nav>
    <a href="/calendar">📅 Calendário</a>
    <a href="/config">⚙ Configurar marca</a>
  </nav>
</header>
<div id="chat">
  <div class="msg agent">Olá! Sou seu agente autônomo de Instagram.

Posso planejar sua semana inteira, gerar imagens com IA, criar legendas estratégicas e publicar tudo automaticamente.

Para começar da forma certa: <strong>configure a identidade da sua agência</strong> em ⚙ Configurar marca — assim todo o conteúdo gerado vai refletir sua marca.

Ou me diga o que fazer agora:</div>
</div>
<footer>
  <form id="form">
    <textarea id="input" placeholder="Ex: Planeje minha semana com foco em cases de sucesso…" rows="1"></textarea>
    <button type="submit" id="btn">↑</button>
  </form>
  <div class="actions">
    <span class="chip" data-msg="Planeje o conteúdo desta semana">📅 Planejar semana</span>
    <span class="chip" data-msg="Como estão as métricas desta semana?">📊 Ver métricas</span>
    <span class="chip" data-msg="Mostre os posts agendados">🗓 Posts agendados</span>
    <span class="chip" data-msg="Crie uma legenda para um post de case de sucesso">✍️ Criar legenda</span>
  </div>
  <div id="hint">Enter para enviar · Shift+Enter para nova linha</div>
</footer>
<script>
const chatEl=document.getElementById('chat'),input=document.getElementById('input'),btn=document.getElementById('btn'),form=document.getElementById('form');
function addMsg(r,t){const el=document.createElement('div');el.className='msg '+r;el.innerText=t;chatEl.appendChild(el);chatEl.scrollTop=chatEl.scrollHeight;return el}
document.querySelectorAll('.chip').forEach(function(chip){chip.addEventListener('click',function(){input.value=chip.dataset.msg;form.dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))})});
form.addEventListener('submit',async function(e){
  e.preventDefault();const text=input.value.trim();if(!text)return;
  addMsg('user',text);input.value='';btn.disabled=true;
  const th=addMsg('thinking','✦ Pensando...');
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
    const d=await r.json();th.remove();
    addMsg('agent',d.reply||d.error||'Erro.');
  }catch(err){th.remove();addMsg('agent','Erro de conexão: '+err.message);}
  finally{btn.disabled=false;input.focus()}
});
input.addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();form.dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))}});
input.addEventListener('input',function(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px'});
</script>
</body>
</html>"""

CALENDAR_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Calendário — Agente Instagram</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#e5e5e5;padding:0}
    header{padding:14px 24px;background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);display:flex;align-items:center;gap:12px}
    header h1{font-size:16px;font-weight:700;color:#fff}
    header a{color:rgba(255,255,255,.8);font-size:12px;text-decoration:none;padding:4px 10px;border-radius:20px;border:1px solid rgba(255,255,255,.3);margin-left:auto}
    main{max-width:900px;margin:32px auto;padding:0 20px}
    h2{font-size:18px;margin-bottom:20px;color:#ccc}
    .card{background:#111;border:1px solid #1e1e1e;border-radius:12px;padding:16px 20px;margin-bottom:12px;display:flex;align-items:flex-start;gap:16px}
    .card img{width:80px;height:80px;object-fit:cover;border-radius:8px;flex-shrink:0;background:#1a1a1a}
    .card-body{flex:1;min-width:0}
    .card-meta{display:flex;gap:10px;align-items:center;margin-bottom:6px}
    .badge{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600}
    .pending{background:#1a2a1a;color:#6fbf73;border:1px solid #2a4a2a}
    .published{background:#1a1a2a;color:#7b8cde;border:1px solid #2a2a4a}
    .failed{background:#2a1a1a;color:#e07070;border:1px solid #4a2a2a}
    .cancelled{background:#1a1a1a;color:#666;border:1px solid #2a2a2a}
    .card-time{font-size:12px;color:#555}
    .card-caption{font-size:13px;color:#aaa;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
    .btn-cancel{background:none;border:1px solid #333;color:#666;font-size:12px;padding:4px 10px;border-radius:6px;cursor:pointer;margin-top:8px}
    .btn-cancel:hover{border-color:#555;color:#aaa}
    .empty{color:#444;text-align:center;padding:60px 0;font-size:15px}
    .filter{display:flex;gap:8px;margin-bottom:20px}
    .filter a{color:#666;font-size:13px;text-decoration:none;padding:5px 14px;border-radius:20px;border:1px solid #2a2a2a;transition:all .15s}
    .filter a:hover,.filter a.active{border-color:#555;color:#ccc}
  </style>
</head>
<body>
<header>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="white" stroke="none"/></svg>
  <h1>📅 Calendário de Publicações</h1>
  <a href="/">← Voltar ao chat</a>
</header>
<main>
  <div class="filter">
    <a href="/calendar" class="active">Todos</a>
    <a href="/calendar?status=pending">Agendados</a>
    <a href="/calendar?status=published">Publicados</a>
    <a href="/calendar?status=failed">Com erro</a>
  </div>
  <div id="posts"></div>
</main>
<script>
const status=new URLSearchParams(location.search).get('status')||'';
fetch('/posts'+(status?'?status='+status:'')).then(r=>r.json()).then(posts=>{
  const el=document.getElementById('posts');
  if(!posts.length){el.innerHTML='<div class="empty">Nenhum post encontrado.</div>';return}
  el.innerHTML=posts.map(p=>`
    <div class="card" id="card-${p.id}">
      ${p.media_url?`<img src="${p.media_url}" onerror="this.style.display='none'">`:''}
      <div class="card-body">
        <div class="card-meta">
          <span class="badge ${p.status}">${p.status}</span>
          <span class="card-time">📅 ${p.scheduled_at?.replace('T',' ')}</span>
          ${p.published_at?`<span class="card-time">✅ ${p.published_at?.replace('T',' ')}</span>`:''}
        </div>
        <div class="card-caption">${(p.caption||'').replace(/</g,'&lt;')}</div>
        ${p.status==='pending'?`<button class="btn-cancel" onclick="cancel(${p.id})">Cancelar</button>`:''}
        ${p.error?`<div style="color:#e07070;font-size:12px;margin-top:4px">Erro: ${p.error}</div>`:''}
      </div>
    </div>`).join('');
});
function cancel(id){
  if(!confirm('Cancelar este post?'))return;
  fetch('/posts/'+id,{method:'DELETE'}).then(r=>r.json()).then(d=>{
    if(d.success)document.getElementById('card-'+id).remove();
  });
}
</script>
</body>
</html>"""

CONFIG_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Configurar Marca — Agente Instagram</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#e5e5e5}
    header{padding:14px 24px;background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);display:flex;align-items:center;gap:12px}
    header h1{font-size:16px;font-weight:700;color:#fff}
    header a{color:rgba(255,255,255,.8);font-size:12px;text-decoration:none;padding:4px 10px;border-radius:20px;border:1px solid rgba(255,255,255,.3);margin-left:auto}
    main{max-width:680px;margin:32px auto;padding:0 20px}
    h2{font-size:18px;margin-bottom:6px;color:#ccc}
    .sub{font-size:13px;color:#555;margin-bottom:28px}
    .field{margin-bottom:20px}
    label{display:block;font-size:13px;color:#bbb;margin-bottom:6px;font-weight:500}
    label small{color:#444;font-weight:400;margin-left:6px}
    input,textarea,select{width:100%;background:#111;border:1px solid #2a2a2a;border-radius:8px;color:#e5e5e5;padding:10px 14px;font-size:13px;outline:none;font-family:inherit}
    input:focus,textarea:focus,select:focus{border-color:#555}
    textarea{resize:vertical;min-height:80px}
    .btn{background:linear-gradient(135deg,#833ab4,#fd1d1d);color:#fff;border:none;border-radius:8px;padding:12px 28px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .15s}
    .btn:hover{opacity:.85}
    #msg{display:none;color:#6fbf73;font-size:13px;margin-left:14px}
  </style>
</head>
<body>
<header>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="white" stroke="none"/></svg>
  <h1>⚙ Configurar Marca</h1>
  <a href="/">← Voltar ao chat</a>
</header>
<main>
  <h2>Identidade da Agência</h2>
  <p class="sub">Configure uma vez — o agente usa isso para gerar todo o conteúdo automaticamente.</p>
  <div class="field">
    <label>Nome da agência</label>
    <input id="agency_name" placeholder="Ex: Studio Digital, Agência Pulsar…">
  </div>
  <div class="field">
    <label>Tom de voz</label>
    <input id="tone" placeholder="Ex: profissional e direto, descontraído mas especialista…">
  </div>
  <div class="field">
    <label>Público-alvo <small>para quem você vende</small></label>
    <input id="target_audience" placeholder="Ex: pequenas e médias empresas, e-commerces, startups…">
  </div>
  <div class="field">
    <label>Temas de conteúdo <small>separados por vírgula</small></label>
    <textarea id="content_topics" placeholder="Ex: marketing digital, cases de sucesso, dicas de tráfego pago, bastidores da agência, tendências…"></textarea>
  </div>
  <div class="field">
    <label>Estilo visual <small>para geração de imagens</small></label>
    <input id="visual_style" placeholder="Ex: minimalista e moderno, vibrante com cores neon, corporativo e elegante…">
  </div>
  <div class="field">
    <label>Melhores horários para postar <small>separados por vírgula</small></label>
    <input id="posting_times" placeholder="Ex: 08:00,12:00,18:00">
  </div>
  <div style="display:flex;align-items:center;margin-top:8px">
    <button class="btn" onclick="save()">Salvar configuração</button>
    <span id="msg">✓ Salvo com sucesso!</span>
  </div>
</main>
<script>
fetch('/api/brand').then(r=>r.json()).then(d=>{
  ['agency_name','tone','target_audience','content_topics','visual_style','posting_times'].forEach(k=>{
    if(d[k])document.getElementById(k).value=d[k];
  });
});
function save(){
  const data={};
  ['agency_name','tone','target_audience','content_topics','visual_style','posting_times'].forEach(k=>{
    data[k]=document.getElementById(k).value.trim();
  });
  fetch('/api/brand',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
    .then(r=>r.json()).then(()=>{
      const m=document.getElementById('msg');m.style.display='inline';
      setTimeout(()=>m.style.display='none',2500);
    });
}
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    import os
    return jsonify({
        "groq_key": "OK" if os.environ.get("GROQ_API_KEY") else "MISSING",
        "instagram_token": "OK" if os.environ.get("INSTAGRAM_ACCESS_TOKEN") else "MISSING",
        "flask_secret": "OK" if os.environ.get("FLASK_SECRET_KEY") else "MISSING",
    })


@app.route("/privacy")
def privacy():
    return """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Política de Privacidade — Agencia.IA</title></head><body style="font-family:sans-serif;max-width:700px;margin:40px auto;padding:0 20px;line-height:1.6">
<h1>Política de Privacidade</h1><p>Última atualização: junho de 2025</p>
<p>A <strong>Agencia.IA</strong> utiliza a API oficial do Instagram (Meta) exclusivamente para gerenciar e publicar conteúdo na própria conta da agência.</p>
<h2>Dados coletados</h2><p>Coletamos apenas dados de desempenho das publicações (alcance, impressões, engajamento) para fins de análise interna.</p>
<h2>Uso dos dados</h2><p>Os dados são utilizados exclusivamente para otimizar a estratégia de conteúdo da agência. Não compartilhamos dados com terceiros.</p>
<h2>Contato</h2><p>Para dúvidas: lucaspigozzi.d@gmail.com</p>
</body></html>"""


@app.route("/")
def index():
    return render_template_string(CHAT_HTML)


@app.route("/calendar")
def calendar():
    return render_template_string(CALENDAR_HTML)


@app.route("/config")
def config():
    return render_template_string(CONFIG_HTML)


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.json or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Mensagem vazia."}), 400

    history = session.get("history", [])
    history.append({"role": "user", "content": message})

    try:
        reply, history = chat(history)
        session["history"] = history[-30:]
        return jsonify({"reply": reply})
    except Exception as e:
        logging.exception("Erro no agente")
        return jsonify({"error": str(e)}), 500


@app.route("/posts")
def list_posts():
    status = request.args.get("status")
    return jsonify(db.list_posts(status))


@app.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    return jsonify({"success": db.cancel_post(post_id)})


@app.route("/api/brand", methods=["GET"])
def get_brand():
    return jsonify(db.get_brand_config())


@app.route("/api/brand", methods=["POST"])
def save_brand():
    db.set_brand_config(request.json or {})
    return jsonify({"success": True})


@app.route("/reset", methods=["POST"])
def reset():
    session.pop("history", None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
