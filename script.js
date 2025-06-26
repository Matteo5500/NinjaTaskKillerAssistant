const chatBox     = document.getElementById('chat-box');
const form        = document.getElementById('chat-form');
const input       = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const avatarVideo = document.getElementById('avatar-video');
const themeToggle = document.getElementById('theme-toggle');


window.onload = () => {
  addMessage('bot', 'Hi! What task should we eat today? 💪🏻');
};


themeToggle.addEventListener('click', () => {
  const newTheme = document.body.dataset.theme === 'light' ? 'dark' : 'light';
  document.body.dataset.theme = newTheme;
  themeToggle.textContent = newTheme === 'light' ? '🌙' : '☀️';
});


document.body.addEventListener('mousemove', (e) => {
  const x = (e.clientX / window.innerWidth  - 0.5) * 20;
  const y = (e.clientY / window.innerHeight - 0.5) * 20;
  avatarVideo.style.transform = `rotateY(${x}deg) rotateX(${-y}deg)`;
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const userText = input.value.trim();
  if (!userText) return;

  addMessage('user', userText);
  input.value = '';

  sendBtn.classList.add('loading');
  avatarVideo.currentTime = 0;
  avatarVideo.play();
  avatarVideo.classList.add('avatar-typing');

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: userText })
    });
    const data = await res.json();

    sendBtn.classList.remove('loading');
    avatarVideo.classList.remove('avatar-typing');
    avatarVideo.pause();
    avatarVideo.currentTime = 0;

    if (data.reply) addMessage('bot', data.reply);
    else addMessage('bot', '⚠️ Oops! Something went wrong.');
  } catch (err) {
    console.error(err);
    sendBtn.classList.remove('loading');
    avatarVideo.classList.remove('avatar-typing');
    avatarVideo.pause();
    avatarVideo.currentTime = 0;
    addMessage('bot', '⚠️ Mission failed. Server error.');
  }
});


function addMessage(sender, text) {
  const msg = document.createElement('div');
  msg.className = `message ${sender}`;
  msg.innerHTML = sender === 'bot'
    ? `<strong>Task Assassin:</strong> ${text}`
    : `<strong>Boss:</strong> ${text}`;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}
