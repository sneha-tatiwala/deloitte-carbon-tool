/* =============================================
   CHAT WIDGET — Deloitte Carbon Intelligence
   open → type → send → typing indicator →
   response → input ready → close → reopen → repeat
   ============================================= */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────
  let isOpen    = false;
  let isWaiting = false;
  const history = [];   // [{role, content}] sent to /api/chat

  // ── Elements ───────────────────────────────────
  const widget      = document.getElementById('cw');
  const bubble      = document.getElementById('cwBubble');
  const panel       = document.getElementById('cwPanel');
  const closeBtn    = document.getElementById('cwClose');
  const messages    = document.getElementById('cwMessages');
  const input       = document.getElementById('cwInput');
  const sendBtn     = document.getElementById('cwSend');
  const suggestions = document.getElementById('cwSuggestions');

  if (!widget || !bubble || !panel) return;

  // ── Suggested questions ────────────────────────
  const SUGGESTED = [
    'What is the ESCert overhang risk for CCTS prices?',
    'How does BEE set compliance targets under CCTS?',
    'What is India\'s MRV capacity gap and why does it matter?',
    'How does CCTS differ from PAT in mechanics and incentives?',
    'What happens under Article 6 ITMO framework for India?',
  ];

  function renderSuggestions() {
    if (!suggestions) return;
    suggestions.innerHTML = `<div class="cw__suggestion-label">Try asking</div>`;
    SUGGESTED.forEach(q => {
      const btn = document.createElement('button');
      btn.className = 'cw__suggestion-btn';
      btn.textContent = q;
      btn.addEventListener('click', () => {
        input.value = q;
        hideSuggestions();
        sendMessage();
      });
      suggestions.appendChild(btn);
    });
  }

  function hideSuggestions() {
    if (suggestions) suggestions.style.display = 'none';
  }

  // ── Open / close ───────────────────────────────
  function openChat() {
    isOpen = true;
    widget.classList.add('chat-open');
    panel.setAttribute('aria-hidden', 'false');
    bubble.setAttribute('aria-expanded', 'true');
    if (history.length === 0) renderSuggestions();
    setTimeout(() => input.focus(), 240);
  }

  function closeChat() {
    isOpen = false;
    widget.classList.remove('chat-open');
    panel.setAttribute('aria-hidden', 'true');
    bubble.setAttribute('aria-expanded', 'false');
  }

  bubble.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && isOpen) closeChat();
  });

  // ── Scroll ──────────────────────────────────────
  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  // ── Render a message ───────────────────────────
  function appendMessage(role, text) {
    const wrapper = document.createElement('div');
    wrapper.className = `cw__msg cw__msg--${role === 'user' ? 'user' : role === 'error' ? 'error' : 'ai'}`;
    const p = document.createElement('p');
    p.textContent = text;
    wrapper.appendChild(p);
    messages.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
  }

  // ── Typing indicator ───────────────────────────
  let typingEl = null;

  function showTyping() {
    typingEl = document.createElement('div');
    typingEl.className = 'cw__typing';
    typingEl.innerHTML = `
      <div class="cw__typing-dots">
        <span></span><span></span><span></span>
      </div>`;
    messages.appendChild(typingEl);
    scrollToBottom();
  }

  function hideTyping() {
    if (typingEl) { typingEl.remove(); typingEl = null; }
  }

  // ── Lock / unlock UI ───────────────────────────
  function setWaiting(val) {
    isWaiting        = val;
    input.disabled   = val;
    sendBtn.disabled = val;
  }

  // ── Send a message ────────────────────────────
  async function sendMessage() {
    const text = input.value.trim();
    if (!text || isWaiting) return;

    hideSuggestions();
    input.value = '';

    appendMessage('user', text);
    history.push({ role: 'user', content: text });

    setWaiting(true);
    showTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.error || `Server error ${res.status}`);
      }

      const reply = data.content ?? '';
      history.push({ role: 'assistant', content: reply });
      hideTyping();
      appendMessage('assistant', reply);

    } catch (err) {
      hideTyping();
      history.pop();
      const msg = err?.message && err.message !== '[object Object]'
        ? err.message
        : 'Something went wrong — please try again.';
      appendMessage('error', msg);
      console.error('[chat]', err);
    }

    setWaiting(false);
    input.focus();
  }

  // ── Event bindings ────────────────────────────
  sendBtn.addEventListener('click', sendMessage);

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // ── Greeting on first open ────────────────────
  const originalOpen = openChat;
  let greeted = false;
  bubble.removeEventListener('click', openChat);
  bubble.addEventListener('click', function () {
    originalOpen();
    if (!greeted) {
      greeted = true;
      setTimeout(() => {
        appendMessage('assistant',
          'This tool covers India\'s CCTS compliance mechanics, the policy database, carbon price signals, sector benchmarks, and Deloitte\'s advisory services in this space. What do you want to know?'
        );
      }, 320);
    }
  });

})();
