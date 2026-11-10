// OFFLINE FALLBACK - Respects on-device Heavy Judge chain
// Heavy 5.6 Codex Hybrid stays as judge/buoy only
// This file makes the dashboard stop lying when bridge is down

(function() {
  'use strict';

  window.OFFLINE_FALLBACK_ACTIVE = true;

  // Patch sendChat if it exists
  const originalSendChat = window.sendChat;

  window.sendChat = async function patchedSendChat() {
    const input = document.getElementById('chatIn');
    if (!input || !input.value.trim()) return;

    const msg = input.value.trim();

    // If bridge is not connected, use local fallback
    if (!window.bridgeConnected) {
      // Local message + respect on-device model chain
      if (typeof window.appendLocalMessage === 'function') {
        window.appendLocalMessage(msg);
      } else {
        // Fallback UI
        const chatLog = document.getElementById('chatLog');
        if (chatLog) {
          const div = document.createElement('div');
          div.className = 'msg local';
          div.innerHTML = `<span class="badge local">LOCAL</span> ${msg}`;
          chatLog.appendChild(div);
          chatLog.scrollTop = chatLog.scrollHeight;
        }
      }
      input.value = '';
      return;
    }

    // Bridge is connected - use original behavior
    if (originalSendChat) {
      return originalSendChat.apply(this, arguments);
    }
  };

  console.log('%c[OfflineFallback] Heavy Judge chain respected. Bridge is optional.', 'color:#ff6b00');
})();